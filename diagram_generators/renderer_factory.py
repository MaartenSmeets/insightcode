# File: diagram_generators/renderer_factory.py

import importlib
import os
import logging
from pathlib import Path

RENDERER_SUFFIX = '_renderer.py'

def get_renderer(diagram_type: str):
    """
    Dynamically load and return the appropriate diagram renderer class based on the diagram type.
    
    The renderer class must follow the naming convention: <DiagramType>Renderer.
    The module file should be named <diagram_type>_renderer.py (e.g., mermaid_renderer.py).
    """
    # Ensure diagram type is lowercase for file matching
    diagram_type = diagram_type.lower()

    # Construct the expected module and class names
    module_name = f'diagram_generators.{diagram_type}_renderer'
    class_name = f'{diagram_type.capitalize()}Renderer'
    
    try:
        # Dynamically import the renderer module
        renderer_module = importlib.import_module(module_name)

        # Dynamically get the renderer class from the module
        renderer_class = getattr(renderer_module, class_name)
        
        logging.info(f"Successfully loaded renderer: {class_name} from {module_name}")
        
        # Return an instance of the renderer class
        return renderer_class()

    except ModuleNotFoundError:
        logging.error(f"Renderer module not found for diagram type: {diagram_type}")
        raise ValueError(f"Unsupported diagram type: {diagram_type}")

    except AttributeError:
        logging.error(f"Renderer class {class_name} not found in module: {module_name}")
        raise ValueError(f"Renderer class {class_name} not found for diagram type: {diagram_type}")
