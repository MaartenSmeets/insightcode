from bs4 import BeautifulSoup
import logging

FILE_EXTENSIONS = ['.html', '.htm', '.xhtml']

def read_file(file_path):
    """Extract text from an HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n')
    except Exception as e:
        logging.error(f"Error reading HTML file {file_path}: {e}")
        return ""
