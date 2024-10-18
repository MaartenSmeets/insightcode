import logging
from pathlib import Path
from config import OUTPUT_DIR, DEFAULT_DIAGRAM_MODEL
from helpers import save_output_to_file
from llm_interface import generate_response_with_llm, DIAGRAM_SYSTEM_PROMPT

# Updated Mermaid Prompt Template with explicit instructions
MERMAID_PROMPT_TEMPLATE = """**Objective:**

Based on the provided codebase summary, generate a concise and professional **Mermaid flowchart** that visually represents the system's architecture, major components, and data flow. Focus on:

- **Logical grouping of components** (e.g., services, databases, external APIs)
- **Interactions** between components and external systems
- **Data flow** between major components

**Instructions:**

- **Use a left-to-right flowchart layout** with inputs (e.g., users) on the left and external systems on the right.
- **Group related components** using subgraphs.
- **Label nodes and edges clearly**, using simple and descriptive names.
- **Avoid special characters**, function names with arguments, parentheses, quotation marks, or any code-specific details in labels.
- **Use only alphanumeric characters and underscores** in labels.
- **Represent external systems distinctly**, and encapsulate all internal components within a grouping named after the codebase.
- **Apply minimal colors** to differentiate logical groupings without overwhelming the diagram.
- **Ensure Mermaid syntax is correct** and the diagram can be rendered without errors.
- **Do not include any additional text** beyond the Mermaid code.
- **Do not include code block markers such as \`\`\`mermaid, \`\`\`, :::mermaid, or :::; provide only the raw Mermaid code**
- **Do not include any explanations, annotations, or text outside the Mermaid code.**
- **Provide only the Mermaid code, without any additional text before or after it.**
- **Do not include comments within the code unless they are necessary for the Mermaid syntax.**

### Example Mermaid Flowchart Syntax:

graph LR
    User[User] --> UI[User_Interface]

    subgraph Codebase
        UI --> Backend[Backend_Service]
        Backend --> API[External_API]
    end

    subgraph External_Systems
        Backend --> DB[Database]
        API --> ThirdParty[Third_Party_System]
    end

This is an example flowchart illustrating a basic system layout, which includes nodes, edges, subgraphs, and external systems.
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