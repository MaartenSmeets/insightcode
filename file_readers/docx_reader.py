import docx
import logging

FILE_EXTENSIONS = ['.docx']

def read_file(file_path):
    """Read contents from a .docx file."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"Error reading docx file {file_path}: {e}")
        return ""
