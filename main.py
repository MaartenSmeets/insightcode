import logging
from pathlib import Path
from config import (
    OUTPUT_DIR,
    DEFAULT_SUMMARIZATION_MODEL,
    OUTPUT_FORMAT,
    GENERATE_DIAGRAM,
    DEFAULT_DIAGRAM_MODEL,
    MAX_FIX_ATTEMPTS,
)
from helpers import generate_unique_filename, save_output_to_file
from file_readers import get_reader
from diagram_generators import generate_diagram_prompt, generate_diagram_code
from diagram_generators.renderer_factory import get_renderer
from llm_interface import summarize_codebase, generate_response_with_llm, DIAGRAM_SYSTEM_PROMPT
import re

def configure_logging():
    """Configure logging with a file handler and console output."""
    log_dir = OUTPUT_DIR
    log_file = log_dir / "script_run.log"

    # Ensure the log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear any existing logging handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up the logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w"),  # File logging
            logging.StreamHandler(),  # Console logging
        ],
    )

def clean_diagram_code(diagram_code: str) -> str:
    """Clean the diagram code by removing code block markers and any additional text."""
    # Remove code block markers such as ```mermaid, ```, :::mermaid, :::
    cleaned_code = re.sub(r'^```.*\n', '', diagram_code, flags=re.MULTILINE)
    cleaned_code = re.sub(r'^```\s*$', '', cleaned_code, flags=re.MULTILINE)
    cleaned_code = re.sub(r'^:::\s*$', '', cleaned_code, flags=re.MULTILINE)
    return cleaned_code.strip()

def fix_diagram_code_with_llm(diagram_code: str, error_message: str) -> str:
    """Use LLM to fix the diagram code based on the error message."""
    # Create a prompt to send to the LLM
    prompt_template = """**Objective:**

Based on the provided diagram code and the error message, fix the diagram code so that it renders correctly.

**Instructions:**

- Review the error message and the diagram code.
- Correct any syntax errors or issues that prevent the diagram from rendering.
- Ensure the corrected diagram code is valid and can be rendered without errors.
- Output only the corrected diagram code.
- **Do not include code block markers such as ``` or :::**
- **Do not include any explanations, comments, annotations, or any text before or after the diagram code.**
- **Provide only the corrected diagram code.**

---

**Input:**
- Diagram code:
{diagram_code}

- Error message:
{error_message}

**Your Task:**
Provide the corrected diagram code.
"""

    prompt = prompt_template.format(diagram_code=diagram_code, error_message=error_message)
    # Use the LLM to generate the fixed diagram code
    fixed_diagram_code = generate_response_with_llm(
        prompt, DIAGRAM_SYSTEM_PROMPT, model=DEFAULT_DIAGRAM_MODEL
    )
    # Clean the fixed diagram code
    fixed_diagram_code = clean_diagram_code(fixed_diagram_code)
    return fixed_diagram_code.strip()

def main():
    """Main function to run the summarization and diagram generation process."""
    # Step 1: Configure logging
    configure_logging()

    # Log when the script starts
    logging.info("Script started.")

    try:
        # Step 2: Set repository directory path
        repo_directory = Path("repo")  # Change to your repository path

        # Step 3: Summarize the codebase
        logging.info("Starting codebase summarization...")
        codebase_summary = summarize_codebase(repo_directory, DEFAULT_SUMMARIZATION_MODEL)

        # Step 4: Check if a summary was generated
        if codebase_summary:
            logging.info("Codebase summary generated successfully.")

            # Step 5: Generate diagram prompt and save it
            logging.info(f"Generating {OUTPUT_FORMAT} diagram prompt...")
            diagram_prompt = generate_diagram_prompt(codebase_summary)

            # Save the diagram prompt to a fixed filename in the output directory
            prompt_filename = f"{OUTPUT_FORMAT}_prompt.txt"
            prompt_filepath = OUTPUT_DIR / prompt_filename
            save_output_to_file(diagram_prompt, prompt_filepath)
            logging.info(f"{OUTPUT_FORMAT.capitalize()} prompt saved to {prompt_filepath}")

            # Step 6: Check if diagram generation is enabled
            if GENERATE_DIAGRAM:
                logging.info(f"Generating {OUTPUT_FORMAT} diagram...")

                # Generate the initial diagram code
                diagram_code = generate_diagram_code(diagram_prompt)

                # Clean the diagram code
                diagram_code = clean_diagram_code(diagram_code)

                # Save the initial diagram code
                diagram_code_filename = f"{OUTPUT_FORMAT}_diagram.txt"
                diagram_code_filepath = OUTPUT_DIR / diagram_code_filename
                save_output_to_file(diagram_code, diagram_code_filepath)

                # Get the appropriate renderer dynamically based on OUTPUT_FORMAT
                renderer = get_renderer(OUTPUT_FORMAT)
                attempt = 0
                success = False
                error_messages = []
                diagram_codes = [diagram_code]

                while attempt < MAX_FIX_ATTEMPTS and not success:
                    try:
                        # Try to render the diagram
                        png_filepath = renderer.generate_png(diagram_codes[-1], OUTPUT_DIR)
                        if png_filepath:
                            logging.info(
                                f"{OUTPUT_FORMAT.capitalize()} diagram PNG generated and saved to {png_filepath}."
                            )
                            success = True
                        else:
                            logging.warning(f"Failed to generate {OUTPUT_FORMAT} diagram PNG.")
                            raise Exception("Rendering returned no PNG filepath.")
                    except Exception as e:
                        attempt += 1
                        error_message = str(e)
                        logging.error(f"Error during rendering attempt {attempt}: {error_message}")
                        error_messages.append(error_message)
                        if attempt < MAX_FIX_ATTEMPTS:
                            logging.info(
                                f"Attempting to fix the diagram code using LLM (Attempt {attempt}/{MAX_FIX_ATTEMPTS})..."
                            )

                            # Use LLM to fix the diagram code
                            fixed_diagram_code = fix_diagram_code_with_llm(
                                diagram_codes[-1], error_message
                            )
                            diagram_codes.append(fixed_diagram_code)

                            # Save the fixed diagram code
                            fixed_diagram_code_filename = (
                                f"{OUTPUT_FORMAT}_diagram_fixed_attempt_{attempt}.txt"
                            )
                            fixed_diagram_code_filepath = OUTPUT_DIR / fixed_diagram_code_filename
                            save_output_to_file(
                                fixed_diagram_code, fixed_diagram_code_filepath
                            )
                            logging.info(
                                f"Fixed {OUTPUT_FORMAT} diagram code saved to {fixed_diagram_code_filepath}"
                            )
                        else:
                            logging.error(
                                "Maximum number of fix attempts reached. Could not generate diagram."
                            )
                            # Save error messages and diagram codes for debugging
                            debug_info = "\n\n".join(
                                [
                                    f"Attempt {i}:\nError Message:\n{em}\n\nDiagram Code:\n{dc}"
                                    for i, (em, dc) in enumerate(
                                        zip(error_messages, diagram_codes), 1
                                    )
                                ]
                            )
                            debug_info_filepath = OUTPUT_DIR / f"{OUTPUT_FORMAT}_debug_info.txt"
                            save_output_to_file(debug_info, debug_info_filepath)
                            logging.info(f"Debug information saved to {debug_info_filepath}")
                if not success:
                    logging.error("Failed to generate diagram after all attempts.")
            else:
                logging.info("Diagram generation is disabled in the configuration.")
        else:
            logging.warning("No relevant files found or summarized.")

    except Exception as e:
        # Log any unexpected errors
        logging.error(f"An error occurred: {e}")

    # Log when the script ends
    logging.info("Script finished.")

if __name__ == "__main__":
    main()
