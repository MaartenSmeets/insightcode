import logging
from pathlib import Path
from config import OUTPUT_DIR
from helpers import save_output_to_file, generate_unique_filename

# Improved PlantUML Prompt Template (without @startuml and @enduml in the prompt itself)
PLANTUML_PROMPT_TEMPLATE = """' Objective:
' Based on the provided detailed codebase summary, generate a concise and professional **PlantUML diagram** that clearly 
' represents the system's architecture, major components, and the data flow between them. Focus on illustrating:
' - The **logical grouping of components** (e.g., services, databases, APIs)
' - **Key interactions** between components and external systems
' - The **data flow** between major components

' Instructions:
' - **Generate valid PlantUML code** that accurately reflects the system architecture.
' - Focus on **major components** and their **functional groupings**.
' - **Avoid mentioning individual files** or technical components (unless external).
' - Use **clear and descriptive labels** for both nodes and interactions.
' - Organize the diagram left-to-right with inputs on the left and external systems on the right.
' - Represent external dependencies clearly (e.g., APIs, databases).
' - Maintain **consistent visual patterns** to differentiate between components, systems, and external dependencies.
' - **Use meaningful labels** to represent the nature of interactions between components.
' - Minimize edge crossings and ensure proper spacing for clarity.

' Diagram Layout:
left to right direction
actor User as user
user --> (System)

' Main components and interactions
{components}
"""

def generate_plantuml_code(combined_summary: str) -> None:
    """Generate PlantUML diagram prompt and save to a file without calling the LLM."""
    # Prepare the PlantUML prompt (without @startuml and @enduml)
    prompt = PLANTUML_PROMPT_TEMPLATE.format(components=combined_summary)

    # Save the prompt to a file in the output directory
    prompt_filename = generate_unique_filename("plantuml_prompt", "txt")
    prompt_filepath = OUTPUT_DIR / prompt_filename
    save_output_to_file(prompt, prompt_filepath)
    logging.info(f"PlantUML prompt saved to {prompt_filepath}")

    # Generate the final diagram with @startuml and @enduml tags
    diagram_code = f"@startuml\n{prompt}\n@enduml"

    # Save the final diagram to a file
    diagram_filename = generate_unique_filename("plantuml_diagram", "puml")
    diagram_filepath = OUTPUT_DIR / diagram_filename
    save_output_to_file(diagram_code, diagram_filepath)
    logging.info(f"PlantUML diagram saved to {diagram_filepath}")
