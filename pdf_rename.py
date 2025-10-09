import os
import fitz
import logging
import tempfile
import pytesseract
from PIL import Image
from datetime import datetime


# Reconfigure these paths as needed
FOLDER_PATH = r"C:\Users\aknap\Projects\Python\test_pdfs"

LOG_FILE_DATE_FORMAT = "%Y-%m-%d"
LOG_MESSAGE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

default_log_path = os.path.join(tempfile.gettempdir(), f"ocr_log_{datetime.now():{LOG_FILE_DATE_FORMAT}}.log")

ERROR_LOG_FILE = os.getenv("PATH_TO_ERROR_LOGS", default_log_path)


ORDER_NUMBER_LENGTH = 8
PDF_EXTENSION = ".pdf"
ORDER_NUMBER_PREFIX = "Order# "
PDF_FILENAME_PREFIX = "Packlist_"

# Set path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"PATH\TO\TESSERACT.EXE"  # Update this path to your Tesseract-OCR installation
# Optionally, you can add Tesseract to your system PATH for easier access

logging.basicConfig(filename=ERROR_LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt=LOG_MESSAGE_DATE_FORMAT)

def log_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            file_path = args[0] if args else "unknown"
            return func(*args, **kwargs)
        except fitz.FileDataError as e:
            logging.exception(f"FileDataError for {func.__name__} for {file_path}: {e}")
        except RuntimeError as e:
            logging.exception(f"RuntimeError for {func.__name__} for {file_path}: {e}")
        except Exception as e:
            logging.exception(f"Error processing {func.__name__} for {file_path}: {e}")
    return wrapper

@log_exceptions
def get_order_number(extracted_text, file_path):
    prefix_index = extracted_text.find(ORDER_NUMBER_PREFIX)

    if prefix_index == -1:
        return
    
    start = prefix_index + len(ORDER_NUMBER_PREFIX)
    end = start + ORDER_NUMBER_LENGTH

    if end > len(extracted_text):
        logging.info(f"Order number extraction failed for {file_path}: insufficient length")
        return
    
    order_number = extracted_text[start:end].strip()
    pdf_directory = os.path.dirname(file_path)
    new_pdf_path = os.path.join(pdf_directory, f"{PDF_FILENAME_PREFIX}{order_number}{PDF_EXTENSION}")
    counter = 1
    while os.path.exists(new_pdf_path):
        new_pdf_path = os.path.join(pdf_directory, f"{PDF_FILENAME_PREFIX}{order_number}({counter}){PDF_EXTENSION}")
        counter += 1

    try:
        os.rename(file_path, new_pdf_path)
        # Uncomment the next line to log successful renames
        # logging.info(f"Renamed {file_path} to {new_pdf_path}")
    except Exception as e:
        logging.info(f"Error renaming {file_path} to {new_pdf_path}: {e}")

@log_exceptions
def process_with_tesseract(file_path):
    with fitz.open(file_path) as doc:
        if doc.page_count == 0:
            logging.info(f"No pages found in {file_path}")
            return

        page = doc[0]
        # Default pixmap rendering was inaccurate, increased resolution for better accuracy
        page_pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
        extracted_text = pytesseract.image_to_string(img).replace("\n", " ")

    get_order_number(extracted_text, file_path)

def main():
    # Ensure the folder exists
    if not os.path.exists(FOLDER_PATH):
        logging.info(f"Folder not found: {FOLDER_PATH}")
        return
    
    # Process each PDF in the folder
    for filename in os.listdir(FOLDER_PATH):
        if filename.lower().endswith(PDF_EXTENSION) and not filename.startswith(PDF_FILENAME_PREFIX):
            file_path = os.path.join(FOLDER_PATH, filename)
            process_with_tesseract(file_path)

if __name__ == "__main__":
    main()
