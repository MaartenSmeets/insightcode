import logging
from odf.opendocument import load
from odf.text import P
from odf.draw import Frame

FILE_EXTENSIONS_TEXT = ['.odt']
FILE_EXTENSIONS_PRESENTATION = ['.odp']

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

def read_odp(file_path):
    """Read contents from an .odp (OpenDocument Presentation) file."""
    try:
        doc = load(file_path)
        full_text = []
        for elem in doc.getElementsByType(Frame):
            text_elem = elem.getElementsByType(P)
            for te in text_elem:
                if te.firstChild:
                    full_text.append(str(te.firstChild.data))
        return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"Error reading odp file {file_path}: {e}")
        return ""