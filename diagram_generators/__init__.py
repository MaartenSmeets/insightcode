import importlib
import logging
from config import OUTPUT_FORMAT

def generate_diagram_prompt(combined_summary: str) -> str:
    """Dynamically load and generate the diagram prompt based on the selected output format."""
    try:
        # Dynamically build the module name (e.g., 'mermaid_generator', 'plantuml_generator')
        module_name = f'diagram_generators.{OUTPUT_FORMAT.lower()}_generator'

        # Load the module dynamically
        generator_module = importlib.import_module(module_name)

        # Dynamically load the prompt generation function (e.g., 'generate_mermaid_prompt')
        generate_prompt_function = getattr(generator_module, f'generate_{OUTPUT_FORMAT.lower()}_prompt')

        # Call the dynamically loaded function
        return generate_prompt_function(combined_summary)

    except ModuleNotFoundError:
        raise ValueError(f"Unsupported output format: {OUTPUT_FORMAT}")

    except AttributeError:
        raise ValueError(f"No valid prompt generator function found for format: {OUTPUT_FORMAT}")

def generate_diagram_code(prompt: str) -> str:
    """Dynamically load and generate the diagram code based on the selected output format."""
    try:
        # Dynamically build the module name (e.g., 'mermaid_generator', 'plantuml_generator')
        module_name = f'diagram_generators.{OUTPUT_FORMAT.lower()}_generator'

        # Load the module dynamically
        generator_module = importlib.import_module(module_name)

        # Dynamically load the diagram code generation function (e.g., 'generate_mermaid_code')
        generate_code_function = getattr(generator_module, f'generate_{OUTPUT_FORMAT.lower()}_code')

        # Call the dynamically loaded function
        return generate_code_function(prompt)

    except ModuleNotFoundError:
        raise ValueError(f"Unsupported output format: {OUTPUT_FORMAT}")

    except AttributeError:
        raise ValueError(f"No valid code generator function found for format: {OUTPUT_FORMAT}")
