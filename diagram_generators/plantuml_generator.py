import logging
from pathlib import Path
from config import OUTPUT_DIR, DEFAULT_DIAGRAM_MODEL
from helpers import save_output_to_file
from llm_interface import generate_response_with_llm, DIAGRAM_SYSTEM_PROMPT

# Improved PlantUML Prompt Template (without @startuml and @enduml in the prompt itself)
PLANTUML_PROMPT_TEMPLATE = """
' **Objective:**
' Based on the provided detailed codebase summary, generate a concise and professional **PlantUML diagram** that clearly 
' represents the system's architecture, major components, and the data flow between them. Ensure the diagram adheres to 
' visualization best practices and architectural visualization standards. Focus on illustrating:
' - The **logical grouping of components** (e.g., services, databases, APIs)
' - **Key interactions** between components and external systems
' - The **data flow** between major components

' **Instructions:**
' - **Generate valid PlantUML code** that accurately reflects the system architecture.
' - Focus on **major components** and their **functional groupings**. Avoid mentioning individual files or overly technical details 
'   unless they are external dependencies.
' - Use **clear and descriptive labels** for both nodes and interactions to enhance understandability for stakeholders.
' - Organize the diagram using a **left-to-right (LR) layout** with inputs (e.g., users) on the left and external systems on the right.
' - Represent external dependencies distinctly (e.g., APIs, databases) using appropriate PlantUML stereotypes or icons.
' - **Use subgraphs** to group related components logically (e.g., different layers or modules of the system).
' - Apply a **consistent visual style** to differentiate between types of components (e.g., services, databases, external systems).
' - **Label edges** to describe the nature of interactions or data flows (e.g., "sends data to", "requests from").
' - **Minimize edge crossings** and ensure proper spacing to maintain diagram clarity and readability.
' - **Avoid special characters** in labels. Use alphanumeric characters and underscores for naming consistency.
' - Do not use quotation marks, parentheses, or mention file extensions and function parameters.
' - **Encapsulate** all internal components within a boundary named after the system. Place external components outside this boundary.
' - **Include the user when relevant** as an actor interacting with the system, positioned on the far left of the diagram.
' - **Use meaningful colors** sparingly to differentiate groups without overwhelming the diagram. Stick to a minimal color palette.
' - Ensure the **PlantUML syntax is correct** and the diagram can be rendered without errors.

' **Diagram Layout Example:**
' @startuml
' left to right direction
' actor User as user
' user --> (System)
' @enduml

---

**Input:**  
- A comprehensive codebase summary in the form: {combined_summary}

**Your Task:**  
Generate a **well-structured and visually appealing** PlantUML diagram that illustrates the system’s architecture and functional data flows based on the provided summary. The output should be valid PlantUML code, with no extra commentary or text beyond the code itself.
"""

def generate_plantuml_prompt(combined_summary: str) -> str:
    """Generate the PlantUML diagram prompt based on the given codebase summary."""
    prompt = PLANTUML_PROMPT_TEMPLATE.format(combined_summary=combined_summary)
    return prompt

def generate_plantuml_code(prompt: str) -> str:
    """Generate PlantUML diagram code based on the provided prompt."""
    # Generate the diagram code by sending the prompt to the LLM
    diagram_code = generate_response_with_llm(prompt, DIAGRAM_SYSTEM_PROMPT, model=DEFAULT_DIAGRAM_MODEL)
    # Wrap the diagram code with @startuml and @enduml
    final_diagram_code = f"@startuml\n{diagram_code}\n@enduml"
    return final_diagram_code  # Ensure a valid string is returned
