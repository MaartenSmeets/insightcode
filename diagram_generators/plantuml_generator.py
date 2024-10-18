import logging
from pathlib import Path
from config import OUTPUT_DIR, DEFAULT_DIAGRAM_MODEL
from llm_interface import generate_response_with_llm, DIAGRAM_SYSTEM_PROMPT

# Updated PlantUML Prompt Template with explicit instructions
PLANTUML_PROMPT_TEMPLATE = """**Objective:**

Based on the provided codebase summary, generate a concise and professional **PlantUML diagram** that visually represents the system's architecture, major components, and data flow. Focus on:

- **Logical grouping of components** (e.g., services, databases, APIs)
- **Key interactions** between components and external systems
- **Data flow** between major components

**Instructions:**

- **Use a left-to-right layout** with inputs (e.g., users) on the left and external systems on the right.
- **Group related components** using boundaries or packages.
- **Label nodes and edges clearly**, avoiding special characters and using alphanumeric characters and underscores.
- **Represent external dependencies distinctly**, using appropriate stereotypes or icons.
- **Encapsulate internal components** within a boundary named after the system.
- **Include the user** as an actor interacting with the system.
- **Apply minimal colors** to differentiate logical groupings without overwhelming the diagram.
- **Avoid mentioning file extensions, function parameters, parentheses, or quotation marks**.
- **Ensure PlantUML syntax is correct** and the diagram can be rendered without errors.
- **Do not include any additional text** beyond the PlantUML code.
- **Do not include code block markers such as ```plantuml, ```, @startuml, @enduml; provide only the raw PlantUML code**

---

**Input:**  
- Codebase summary: {combined_summary}

**Your Task:**  
Generate valid PlantUML code that illustrates the system's architecture and data flows based on the provided summary. Output only the PlantUML code."""

def generate_plantuml_prompt(combined_summary: str) -> str:
    """Generate the PlantUML diagram prompt based on the given codebase summary."""
    prompt = PLANTUML_PROMPT_TEMPLATE.format(combined_summary=combined_summary)
    return prompt

def generate_plantuml_code(prompt: str) -> str:
    """Generate PlantUML diagram code based on the provided prompt."""
    # Generate the diagram code by sending the prompt to the LLM
    diagram_code = generate_response_with_llm(prompt, DIAGRAM_SYSTEM_PROMPT, model=DEFAULT_DIAGRAM_MODEL)
    return diagram_code  # Ensure a valid string is returned
