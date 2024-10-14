import logging
from odf.opendocument import load
from odf.text import P

FILE_EXTENSIONS = ['.odt']

def read_odt(file_path):
    """Read contents from an .odt (OpenDocument Text) file."""
    try:
        doc = load(file_path)
        full_text = []
        for elem in doc.getElementsByType(P):
            if elem.firstChild:
                full_text.append(str(elem.firstChild.data))
        return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"Error reading odt file {file_path}: {e}")
        return ""