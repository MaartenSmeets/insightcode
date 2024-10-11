import pdfplumber
import logging
import fitz  # PyMuPDF for PDF image extraction
import pytesseract
from PIL import Image

FILE_EXTENSIONS = ['.pdf']

def read_file(file_path):
    """Extract text from a PDF file, using OCR if necessary."""
    try:
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        if not text.strip():
            # If no text was extracted, use OCR
            logging.info(f"No text extracted from {file_path}, performing OCR.")
            text = ocr_pdf_file(file_path)
        return text
    except Exception as e:
        logging.error(f"Error reading PDF file {file_path}: {e}")
        return ""

def ocr_pdf_file(file_path):
    """Perform OCR on a PDF file."""
    try:
        text = ''
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logging.error(f"Error performing OCR on PDF file {file_path}: {e}")
        return ""
