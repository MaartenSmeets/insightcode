import logging
from pathlib import Path
from config import OLLAMA_URL, DEFAULT_SUMMARIZATION_MODEL, CACHE_DIR, OUTPUT_DIR
from helpers import save_output_to_file, generate_unique_filename
from file_readers import get_reader
import requests
import json
import shelve
from hashlib import md5

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# File Summary Prompt Template
FILE_SUMMARY_PROMPT_TEMPLATE = """
**Task**: Provide a concise and factual summary of the following file's content in **English**, focusing on its purpose and functionality.

**Important Instructions**:
- **Do not generate or write any code**: Avoid providing code snippets, sample implementations, or any form of code.
- **Do not offer suggestions, improvements, or critiques**: Do not analyze the code for potential enhancements or provide feedback.
- **Do not explain how to accomplish tasks**: Refrain from giving instructions or methods for implementation.
- **Avoid detailed code explanations**: Do not translate code logic into step-by-step descriptions.
- **Do not include any code elements**: Omit specific variable names, function names, or code-specific details unless essential for understanding.
- **Focus on high-level aspects**: Concentrate on the overall purpose and functionality without delving into implementation details.

**Do not include any code snippets, code examples, implementation details, suggestions, critiques, or recommendations in your response.**

---

**File Path**: {file_path}

**File Content**:

{file_content}

---

**Your Summary**:
"""

# System prompt to control behavior of the LLM
SYSTEM_PROMPT = """
You are an assistant that summarizes code files by providing concise, high-level overviews without including any code or technical details. Focus on describing the purpose, functionality, and interactions of the code without generating or suggesting code.
"""

def init_cache() -> shelve.Shelf:
    """Initialize the shelve cache."""
    logging.debug("Initializing cache directory")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return shelve.open(str(CACHE_DIR / 'llm_cache.db'))

def generate_cache_key(prompt: str, model: str) -> str:
    """Generate a unique hash for cache key based on input."""
    key_string = f"{model}_{prompt}"
    cache_key = md5(key_string.encode()).hexdigest()
    logging.debug(f"Generated cache key: {cache_key} for prompt: {prompt[:50]}")
    return cache_key

def generate_response_with_llm(prompt: str, model: str) -> str:
    """Call the LLM via API to generate responses with caching."""
    cache = init_cache()
    cache_key = generate_cache_key(prompt, model)

    # Check if the result is already cached
    if cache_key in cache:
        logging.info(f"Fetching result from cache for prompt: {prompt[:50]}...")
        response_content = cache[cache_key]
        cache.close()
        return response_content

    # If not cached, call the LLM API
    try:
        logging.info(f"Sending request to LLM with model '{model}' and prompt size {len(prompt)}")

        # Use 'prompt' instead of 'messages' in the payload
        payload = {
            "model": model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT
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
        prompt = FILE_SUMMARY_PROMPT_TEMPLATE.format(file_path=file_path, file_content=file_content)
        
        # Generate the summary using the LLM
        try:
            summary = generate_response_with_llm(prompt, summarization_model)
            if summary:
                # Save each summary in the summaries directory with a unique filename
                summary_filename = generate_unique_filename(file_path.stem, "txt")
                summary_file_path = summaries_dir / summary_filename
                save_output_to_file(summary, summary_file_path)
                logging.info(f"Summary saved to {summary_file_path}")

                # Add to the combined summary with the filename
                combined_summary.append(f"Filename: {file_path}\n{summary}\n")
        except Exception as e:
            logging.error(f"Error generating summary for file {file_path}: {e}")
            continue

        # Log progress in percentage
        progress_percentage = (idx / total_files) * 100
        logging.info(f"Progress: {progress_percentage:.2f}% ({idx}/{total_files} files processed)")

    # Combine all summaries and return
    return "\n".join(combined_summary)
