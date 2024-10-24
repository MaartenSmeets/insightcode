import chardet
import logging

# Expanded list of file extensions
FILE_EXTENSIONS = [
    '.txt', '.md', '.py', '.java', '.js', '.ts',
    '.css', '.c', '.cpp', '.h', '.json', '.xml', '.yml', '.yaml', '.conf', '.ini', '.log', 
    '.j2', '.tf', '.tfvars', '.properties', '.jsp', '.do', '.mvc', '.config'
]

def read_file(file_path):
    """Read plain text files with proper encoding."""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read(10000)
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] else 'utf-8'

        with open(file_path, 'r', encoding=encoding, errors='replace') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error reading text file {file_path}: {e}")
        return ""