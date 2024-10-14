import logging
from pathlib import Path
from config import OUTPUT_DIR, DEFAULT_DIAGRAM_MODEL
from helpers import save_output_to_file
from llm_interface import generate_response_with_llm, DIAGRAM_SYSTEM_PROMPT

# Mermaid Prompt Template
MERMAID_PROMPT_TEMPLATE = """**Objective:**

Based on the provided codebase summary, generate a concise and professional **Mermaid flowchart** that visually represents the system's architecture, major components, and data flow. Focus on:

- **Logical grouping of components** (e.g., services, databases, external APIs)
- **Interactions** between components and external systems
- **Data flow** between major components

**Instructions:**

- **Use a left-to-right flowchart layout** with inputs (e.g., users) on the left and external systems on the right.
- **Group related components** using subgraphs.
- **Label nodes and edges clearly**, avoiding special characters and using alphanumeric characters and underscores.
- **Represent external systems distinctly**, and encapsulate all internal components within a grouping named after the codebase.
- **Apply minimal colors** to differentiate logical groupings without overwhelming the diagram.
- **Avoid mentioning file extensions, function parameters, parentheses, or quotation marks**.
- **Ensure Mermaid syntax is correct** and the diagram can be rendered without errors.
- **Do not include any additional text** beyond the Mermaid code.

---

**Input:**  
- Codebase summary: {combined_summary}

**Your Task:**  
Generate valid Mermaid code that illustrates the system's architecture and data flows based on the provided summary. Output only the Mermaid code.
"""

def generate_mermaid_prompt(combined_summary: str) -> str:
    """Generate the Mermaid diagram prompt based on the given codebase summary."""
    prompt = MERMAID_PROMPT_TEMPLATE.format(combined_summary=combined_summary)
    return prompt

def generate_mermaid_code(prompt: str) -> str:
    """Generate Mermaid diagram code based on the provided prompt."""
    # Generate the diagram code by sending the prompt to the LLM
    diagram_code = generate_response_with_llm(prompt, DIAGRAM_SYSTEM_PROMPT, model=DEFAULT_DIAGRAM_MODEL)
    return diagram_code  # Ensure a valid string is returned
