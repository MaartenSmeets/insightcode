import logging
from pathlib import Path
from config import OLLAMA_URL, DEFAULT_SUMMARIZATION_MODEL, CACHE_DIR, OUTPUT_DIR, CLEAN_CACHE_ON_STARTUP
from helpers import save_output_to_file, generate_unique_filename, is_irrelevant_file
from file_readers import get_reader
import requests
import json
import shelve
from hashlib import md5
import shutil

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# File Summary Prompt Template

FILE_SUMMARY_PROMPT_TEMPLATE = """
You are tasked with providing a **precise**, **comprehensive**, and **well-structured** English summary of a file from a software repository. Focus solely on summarizing the content of the file without generating or modifying any code. Do not include code snippets, feedback, or suggestions. Avoid speculative comments, recommendations, or potential improvements.

The summary must be:
- **Factual and objective**: Include only verifiable information directly based on the file’s contents. Avoid assumptions, interpretations, or unsubstantiated conclusions.
- **Specific and relevant**: Refer directly to the actual contents of the file. Focus on its purpose, functionality, and role within the broader system, avoiding unrelated information or generalizations.
- **Concise yet complete**: Capture all essential details without redundancy. The summary should be clear, succinct, and free of unnecessary information.

When applicable, address the following relevant aspects:
- **Purpose and functionality**: Summarize the core purpose of the file and what functionality it provides within the overall project.
- **Key components**: Highlight critical elements such as functions, classes, or modules and explain their roles.
- **Inputs and outputs**: Mention any inputs processed by the file and the outputs it generates.
- **Dependencies**: Identify external or internal dependencies (e.g., libraries, APIs, or other files) and explain their usage.
- **Data flow**: Describe how data is processed, transformed, or manipulated within the file.
- **Interactions**: Explain how the file interacts with other components or systems.

Your goal is to offer enough detail to give a clear understanding of the file’s role and its function within the codebase, without unnecessary elaboration.

**File being summarized**: {file_path}

**File content**:
{file_content}

**Your task**
Remember, your task is to summarize the **file’s content only** without generating any code or giving suggestions.
"""

# System prompt to control behavior of the LLM
SYSTEM_PROMPT = """
You are a code summarization assistant. Your task is to provide **concise, high-level summaries** of code files. Focus on describing the file’s **purpose**, **functionality**, and **role** within the broader project. 
- **Do not generate or modify code**.
- **Do not include any technical details** such as specific variable names, functions, or code structure.
- **Avoid feedback, suggestions, or explanations** about how the code works or potential improvements.

Your summaries should remain focused on the **high-level intent** and interactions of the file within the system, ensuring they are clear, concise, and free from implementation details.
"""

DIAGRAM_SYSTEM_PROMPT = """You are a diagram code generation assistant. Your task is to generate valid and accurate diagram code in either PlantUML or Mermaid format, based solely on the provided prompts.

### Guidelines:

- **Do not include any explanations, comments, or additional text**; output only the diagram code.
- **Ensure the diagram code is syntactically correct** and adheres to the standards of the specified diagram language.
- **Focus on accurately representing** the provided summary or instructions in the diagram code.
- **Use appropriate syntax and conventions** for the specified diagram language.
- **Avoid special characters** in labels; use only alphanumeric characters and underscores.
- **Do not include file extensions, function parameters, or specific implementation details** unless explicitly requested.
- **Provide only the raw diagram code**, without wrapping it in markdown or code blocks.

Your response should consist solely of the diagram code.
"""

def clean_cache():
    """Clean the cache by removing the cache directory if it exists."""
    if CACHE_DIR.exists() and CACHE_DIR.is_dir():
        logging.info("Cleaning cache directory...")
        shutil.rmtree(CACHE_DIR)
        logging.info("Cache directory cleaned.")

def init_cache() -> shelve.Shelf:
    """Initialize the shelve cache."""
    logging.debug("Initializing cache directory")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return shelve.open(str(CACHE_DIR / 'llm_cache.db'))

def generate_cache_key(user_prompt: str, system_prompt: str, model: str) -> str:
    """Generate a unique hash for cache key based on input."""
    key_string = f"{model}_{system_prompt}_{user_prompt}"
    cache_key = md5(key_string.encode()).hexdigest()
    logging.debug(f"Generated cache key: {cache_key} for prompt: {user_prompt[:50]}")
    return cache_key

def generate_response_with_llm(user_prompt: str, system_prompt: str, model: str) -> str:
    """Call the LLM via API to generate responses with caching."""
    if CLEAN_CACHE_ON_STARTUP:
        clean_cache()
    cache = init_cache()
    cache_key = generate_cache_key(user_prompt, system_prompt, model)

    # Check if the result is already cached
    if cache_key in cache:
        logging.info(f"Fetching result from cache for prompt: {user_prompt[:50]}...")
        response_content = cache[cache_key]
        cache.close()
        return response_content

    # If not cached, call the LLM API
    try:
        logging.info(f"Sending request to LLM with model '{model}' and prompt size {len(user_prompt)}")

        # Build the full prompt as per Llama's expected format

        payload = {
            "model": model,
            "prompt": user_prompt,
            "system": system_prompt
        }

        logging.debug(f"Payload: {json.dumps(payload)}")

        headers = {'Content-Type': 'application/json'}
        response = requests.post(OLLAMA_URL, data=json.dumps(payload), headers=headers, stream=True)

        logging.debug(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"Failed to generate response with LLM: HTTP {response.status_code}")
            logging.debug(f"Response content: {response.text}")
            cache.close()
            return ""

        # Read the streaming response
        response_content = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    # Check if 'response' field is present
                    if 'response' in data:
                        response_content += data['response']
                    if data.get('done', False):
                        break
                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError: {e}")
                    logging.debug(f"Line content: {line}")
                    continue

        if not response_content:
            logging.warning("Unexpected response or no response.")
            logging.debug(f"Complete raw response: {response.text}")
            cache.close()
            return ""

        # Cache the result
        logging.debug("Caching the generated response.")
        cache[cache_key] = response_content
        cache.close()

        return response_content

    except Exception as e:
        logging.error(f"Failed to generate response with LLM: {e}")
        cache.close()
        raise e
    

def summarize_codebase(directory: Path, summarization_model: str = DEFAULT_SUMMARIZATION_MODEL) -> str:
    """Summarize the entire repository and save individual summaries with unique filenames."""

    # Create a directory for saving individual summaries
    summaries_dir = OUTPUT_DIR / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    all_files = [f for f in directory.glob('**/*') if f.is_file()]
    total_files = len(all_files)
    combined_summary = []

    logging.info(f"Starting codebase summarization... Total files to process: {total_files}")

    # Process each file and save the summaries
    for idx, file_path in enumerate(all_files, start=1):
        if is_irrelevant_file(file_path):
            logging.info(f"Skipping irrelevant file: {file_path}")
            continue

        file_extension = file_path.suffix
        reader = get_reader(file_extension)
        logging.info(f"Processing file {idx}/{total_files} ({file_path.name}) with reader for extension {file_extension}")

        # Read file content
        try:
            file_content = reader(file_path)
            logging.debug(f"Read content from file {file_path}")
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            continue

        # Prepare the prompt for summarization
        user_prompt = FILE_SUMMARY_PROMPT_TEMPLATE.format(file_path=file_path, file_content=file_content)

        # Generate the summary using the LLM
        try:
            summary = generate_response_with_llm(user_prompt, SYSTEM_PROMPT, summarization_model)
            if summary:
                # Save each summary in the summaries directory with a unique filename
                summary_filename = generate_unique_filename(file_path.stem, "txt")
                summary_file_path = summaries_dir / summary_filename
                save_output_to_file(summary, summary_file_path)
                logging.info(f"Summary saved to {summary_file_path}")

                # Add to the combined summary with the filename
                combined_summary.append(f"Filename: {file_path}\n{summary}\n")
            else:
                logging.warning(f"No summary generated for {file_path}")
        except Exception as e:
            logging.error(f"Error generating summary for file {file_path}: {e}")
            continue

        # Log progress in percentage
        progress_percentage = (idx / total_files) * 100
        logging.info(f"Progress: {progress_percentage:.2f}% ({idx}/{total_files} files processed)")

    # Combine all summaries and return
    return "\n".join(combined_summary)
