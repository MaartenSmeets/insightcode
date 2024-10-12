import logging
from pathlib import Path
from config import OUTPUT_DIR, DEFAULT_DIAGRAM_MODEL
from helpers import save_output_to_file
from llm_interface import generate_response_with_llm, DIAGRAM_SYSTEM_PROMPT

# Mermaid Prompt Template
MERMAID_PROMPT_TEMPLATE = """**Objective:**
Based on the provided detailed codebase summary, generate a concise professional **Mermaid diagram** that clearly and concisely represents the system's 
architecture, major components, and data flow in a visually appealing and easy-to-understand manner. Focus on illustrating 
the **logical grouping of components**, their **interactions**, and the **data flow** between both internal and external 
systems. Make sure not to use special characters. You are only allowed in names, groupings, edges, nodes, etc., to use 
alphanumeric characters. Also avoid mentioning file extensions and function parameters. Do not use parentheses. 
Do not use quotation marks. Avoid mentioning filenames directly and use a functional name instead. Add the user as an entity 
who interacts with the analyzed code. The user should be on the left of the diagram and external dependencies on the right.

**Instructions:**

- **Generate valid Mermaid code** that accurately reflects the system architecture.
- Focus on **major components** and their **functional groupings**. Avoid mentioning individual files and solely technical components such as DAOs and configuration (unless they are an external dependency). Do not be overly detailed but stick to a high-level overview.
- Use **clear, descriptive labels** for both nodes and edges to make the diagram intuitive for stakeholders.
- **Organize components into subgraphs** or groups based on logical relationships (e.g., services, databases, external APIs) to provide a clear and structured view.
- Use **distinct but not overly bright colors** in the diagram to differentiate logical groups.
- Use a flowchart with left to right layout for enhanced readability. Inputs should be on the left and external services/systems which are called should be on the right.
- Maintain **consistent visual patterns** to distinguish between types of components.
- **Apply a minimal color scheme** to differentiate between logical groupings, system layers, or types of components, keeping the design professional.
- Use **edge labels** to describe the nature of interactions or data flow between components (e.g., "sends data", "receives response", "queries database").
- **Minimize crossing edges** and ensure proper spacing to avoid clutter and maintain clarity.
- Ensure the Mermaid syntax is correct, and the diagram can be rendered without errors.
- Avoid setting an element to be a parent of itself.
- Encapsulate all components which are part of the repository-supplied code by the name of the code. Place external components/systems inside their own encapsulation (for example systems/components like mail servers, LDAP providers, databases).

---

**Input:**  
- A comprehensive codebase summary in the form: {combined_summary}

**Your Task:**  
Generate a **well-structured and visually appealing** Mermaid diagram that illustrates the system’s architecture and functional data flows based on the provided summary. The output should be valid Mermaid code, with no extra commentary or text beyond the code itself.
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
