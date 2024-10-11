import importlib
import logging
from config import OUTPUT_FORMAT

def generate_diagram(combined_summary: str) -> str:
    """Dynamically load and generate a diagram based on the selected output format."""
    try:
        # Dynamically build the module name (e.g., 'mermaid_generator', 'plantuml_generator')
        module_name = f'diagram_generators.{OUTPUT_FORMAT}_generator'
        
        # Load the module dynamically
        generator_module = importlib.import_module(module_name)
        
        # Dynamically load the generator function (e.g., 'generate_mermaid_code', 'generate_plantuml_code')
        generate_function = getattr(generator_module, f'generate_{OUTPUT_FORMAT}_code')
        
        # Call the dynamically loaded function
        return generate_function(combined_summary)
    
    except ModuleNotFoundError:
        raise ValueError(f"Unsupported output format: {OUTPUT_FORMAT}")
    
    except AttributeError:
        raise ValueError(f"No valid generator function found for format: {OUTPUT_FORMAT}")
