import os
import fitz
import tempfile
import pytesseract
from PIL import Image
from datetime import datetime

# Reconfigure these paths as needed
FOLDER_PATH = os.getenv("PDF_INPUT_PATH", "path/to/input")

default_log_path = os.path.join(tempfile.gettempdir(), f"ocr_log_{datetime.now():%Y-%m-%d}.log")
ERROR_LOG_FILE = os.getenv("PATH_TO_ERROR_LOGS", default_log_path)

ORDER_NUMBER_PREFIX = "Order# "
PDF_FILENAME_PREFIX = "Packlist_"
PDF_EXTENSION = ".pdf"

# Set path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = "PATH/TO/TESSERACT_EXECUTABLE"  # e.g., "/usr/bin/tesseract"
# Optionally, you can add Tesseract to your system PATH for easier access

def log_messages(message):
    # Log messages to a file with timestamps
    try:
        with open(ERROR_LOG_FILE, "a") as log_file:
            log_file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {message}\n")
    except Exception as e:
        print(f"Failed to log message: {e}")


def process_with_tesseract(file_path):
    try:
       
        # Open the PDF and convert the first page to an image
        with fitz.open(file_path) as doc:
           
            # Check if the document has pages
            if doc.page_count == 0:
                log_messages(f"No pages found in {file_path}")
                return

            # Only process the first page
            page = doc[0]
            # Default pixmap rendering was inaccurate, increased resolution for better accuracy
            # Adjust higher if needed
            page_pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
            extracted_text = pytesseract.image_to_string(img).replace("\n", " ")

        index = extracted_text.find(ORDER_NUMBER_PREFIX)

        # Extract the order number and rename the file
        if index != -1 and index + len(ORDER_NUMBER_PREFIX) + 8 <= len(extracted_text):
            order_number = extracted_text[index + len(ORDER_NUMBER_PREFIX): index + len(ORDER_NUMBER_PREFIX) + 8]
            pdf_directory = os.path.dirname(file_path)
            new_pdf_path = os.path.join(pdf_directory, f"{PDF_FILENAME_PREFIX}{order_number}{PDF_EXTENSION}")
            counter = 1
            while os.path.exists(new_pdf_path):
                new_pdf_path = os.path.join(pdf_directory, f"{PDF_FILENAME_PREFIX}{order_number}({counter}){PDF_EXTENSION}")
                counter += 1
            
            try:
                os.rename(file_path, new_pdf_path)
            except Exception as e:
                log_messages(f"Error renaming {file_path} to {new_pdf_path}: {e}")
            # Uncomment the next line to log successful renames
            # log_messages(f"Renamed {file_path} to {new_pdf_path}")
        
        else:
            log_messages(f"Order number not found in {file_path}")

    except fitz.FileDataError as e:
        log_messages(f"FileDataError for {file_path}: {e}")

    except RuntimeError as e:
        log_messages(f"RuntimeError for {file_path}: {e}")

    except Exception as e:
        log_messages(f"Error processing {file_path}: {e}")

def main():
    # Ensure the folder exists
    if not os.path.exists(FOLDER_PATH):
        log_messages(f"Folder not found: {FOLDER_PATH}")
        return
    
    # Process each PDF in the folder
    for filename in os.listdir(FOLDER_PATH):
        if filename.lower().endswith(PDF_EXTENSION) and not filename.startswith(PDF_FILENAME_PREFIX):
            file_path = os.path.join(FOLDER_PATH, filename)
            process_with_tesseract(file_path)

if __name__ == "__main__":
    main()
