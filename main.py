import logging
from pathlib import Path
from config import OUTPUT_DIR, DEFAULT_SUMMARIZATION_MODEL, OUTPUT_FORMAT
from helpers import generate_unique_filename, save_output_to_file
from file_readers import get_reader
from diagram_generators import generate_diagram
from llm_interface import summarize_codebase

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
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),  # File logging
            logging.StreamHandler()  # Console logging
        ]
    )

def main():
    """Main function to run the summarization and diagram generation process"""
    # Step 1: Configure logging
    configure_logging()

    # Log when the script starts
    logging.info("Script started.")

    try:
        # Step 2: Set repository directory path
        repo_directory = Path('repo')  # Change to your repository path

        # Step 3: Summarize the codebase
        logging.info("Starting codebase summarization...")
        codebase_summary = summarize_codebase(repo_directory, DEFAULT_SUMMARIZATION_MODEL)

        # Step 4: Check if a summary was generated
        if codebase_summary:
            logging.info("Codebase summary generated successfully.")
            
            # Step 5: Generate diagram based on the chosen output format
            logging.info(f"Generating {OUTPUT_FORMAT} diagram...")
            diagram_code = generate_diagram(codebase_summary)

            # Save the diagram file with the correct extension based on the format
            diagram_file = generate_unique_filename("architecture_diagram", OUTPUT_FORMAT)
            save_output_to_file(diagram_code, OUTPUT_DIR / diagram_file)

            logging.info(f"{OUTPUT_FORMAT.capitalize()} diagram generated and saved to {diagram_file}.")
        else:
            logging.warning("No relevant files found or summarized.")
    
    except Exception as e:
        # Log any unexpected errors
        logging.error(f"An error occurred: {e}")

    # Log when the script ends
    logging.info("Script finished.")

if __name__ == "__main__":
    main()
