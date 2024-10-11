import logging
from pathlib import Path
from config import OLLAMA_URL, DEFAULT_SUMMARIZATION_MODEL, CACHE_DIR, OUTPUT_DIR
from helpers import save_output_to_file, generate_unique_filename
from file_readers import get_reader
import requests
import json
import shelve
from hashlib import md5

# File Summary Prompt Template
FILE_SUMMARY_PROMPT_TEMPLATE = """You are tasked with summarizing a file from a software repository. Provide only a **precise**, **comprehensive**, and **well-structured** **English language** summary that accurately reflects the contents of the file. Do not write or update code. Do not generate code to create a summary but create a summary. Do not ask for confirmation. Do not provide suggestions. Do not provide recommendations. Do not mention potential improvements. Do not mention considerations. Do not mention what you are not certain of. Do not mention the document or file. Focus solely on creating the summary. Avoid redundancy and do not summarize the summary. The summary must be:

- **Factual and objective**: Include only verifiable information based on the provided file. Avoid any assumptions, opinions, interpretations, or speculative conclusions.
- **Specific and relevant**: Directly reference the actual contents of the file. Avoid general statements or unrelated information. Focus on the specific purpose, functionality, and structure of the file.
- **Concise yet complete**: Ensure that the summary captures all essential details while being succinct. Eliminate redundancy and unnecessary information.

In particular, address the following when applicable and relevant to the file’s role in the codebase. When not applicable, leave out the section:
- **Purpose and functionality**: Describe the file's core purpose, what functionality it implements, and how it fits into the broader system.
- **Key components**: Highlight any critical functions, classes, methods, or modules defined in the file and explain their roles.
- **Inputs and outputs**: Explicitly mention any input data or parameters the file processes, and describe the outputs it generates.
- **Dependencies**: Identify any internal or external dependencies (e.g., libraries, APIs, other files) and explain how they are used in the file.
- **Data flow**: Describe the flow of data through the file, including how data is processed, transformed, or manipulated.
- **Interactions**: If applicable, detail how this file interacts with other parts of the system or external systems.

Your summary should provide enough detail to give a clear understanding of the file’s purpose and its function within the codebase, without adding unnecessary explanations or speculative content.

**File being summarized**: {file_path}
{file_content}

***Your task**
Your goal is to only create a summary in English of the file's purpose, functionality, key components, inputs/outputs, dependencies, data flow, and interactions, ensuring the summary is factual, specific, relevant, and concise.
"""

def init_cache() -> shelve.Shelf:
    """Initialize the shelve cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return shelve.open(str(CACHE_DIR / 'llm_cache.db'))

def generate_cache_key(prompt: str, model: str) -> str:
    """Generate a unique hash for cache key based on input."""
    key_string = f"{model}_{prompt}"
    return md5(key_string.encode()).hexdigest()

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
        payload = {"model": model, "prompt": prompt}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(OLLAMA_URL, data=json.dumps(payload), headers=headers, stream=True)

        if response.status_code != 200:
            logging.error(f"Failed to generate response with LLM: HTTP {response.status_code}")
            cache.close()
            return ""

        response_content = ""
        for line in response.iter_lines():
            if line:
                try:
                    line_json = json.loads(line.decode('utf-8'))
                    response_text = line_json.get('response', '')
                    response_content += response_text
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse line as JSON: {e}")
                    continue

        if not response_content:
            logging.warning("Unexpected response or no response.")
            cache.close()
            return ""

        # Cache the result
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
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            continue

        # Prepare the prompt for summarization
        prompt = f"Summarize the following file: {file_path}\n\n{file_content}"
        
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