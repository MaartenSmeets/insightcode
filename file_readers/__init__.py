import os
import glob
import importlib
import logging

# Initialize a registry of readers
readers = {}

def default_reader(file_path):
    logging.debug(f"No specific reader for file extension, using default text reader for {file_path}")
    from .text_reader import read_file as read_text_file
    return read_text_file(file_path)

# Dynamically import all modules in the current directory
module_dir = os.path.dirname(__file__)
module_files = glob.glob(os.path.join(module_dir, '*.py'))

for module_file in module_files:
    module_name = os.path.basename(module_file)[:-3]
    if module_name == '__init__':
        continue
    module = importlib.import_module(f'.{module_name}', package=__package__)
    if hasattr(module, 'FILE_EXTENSIONS') and hasattr(module, 'read_file'):
        for ext in module.FILE_EXTENSIONS:
            readers[ext.lower()] = module.read_file

def get_reader(file_extension):
    return readers.get(file_extension.lower(), default_reader)
