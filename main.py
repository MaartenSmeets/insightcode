import os 
import shelve
import uuid
import logging
import traceback
import shutil
import json
import requests
import re
from hashlib import md5
from datetime import datetime

# Import get_reader from file_readers
from file_readers import get_reader

# Constants and Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"  # Configurable Ollama URL

DEFAULT_SUMMARIZATION_MODEL = 'llama3.1:8b-instruct-fp16'
SUMMARIZATION_MODEL_TOKENIZER = 'meta-llama/Llama-3.1-8B-Instruct'

CACHE_DIR = 'cache'
OUTPUT_DIR = "output"  # Single directory for all generated content
MERMAID_PROMPT_FILE = os.path.join(OUTPUT_DIR, "mermaid_prompt.txt")

# Subdirectories within OUTPUT_DIR
SUMMARIES_DIR = os.path.join(OUTPUT_DIR, "summaries")
UNPROCESSED_DIR = os.path.join(OUTPUT_DIR, "unprocessed_files")

# Logging Configuration
log_file = 'script_run.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file, mode='w'), logging.StreamHandler()]
)

# Prompt Templates
DEFAULT_MERMAID_PROMPT_TEMPLATE = """**Objective:**
Based on the provided detailed codebase summary, generate a concise professional **Mermaid diagram** that clearly and concisely represents the system's 
architecture, major components, and data flow in a visually appealing and easy-to-understand manner. Focus on illustrating 
the **logical grouping of components**, their **interactions**, and the **data flow** between both internal and external 
systems. Make sure not to use special characters. You are only allowed in names, groupings, edges, nodes, etc., to use 
alphanumeric characters. Also avoid mentioning file extensions and function parameters. Do not use parentheses. 
Do not use quotation marks. Avoid mentioning filenames directly and use a functional name instead. Add the user as an entity 
who interacts with the analysed code. The user should be on the left of the diagram and external dependencies on the right.

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
- Encapsulate all components which are part of the repository supplied code by the name of the code. Place external components/systems inside their own encapsulation (for example systems/components like mailservers, LDAP providers, databases).

---

**Input:**  
- A comprehensive codebase summary in the form: {combined_summary}

**Your Task:**  
Generate a **well-structured and visually appealing** Mermaid diagram that illustrates the system’s architecture and functional data flows based on the provided summary. The output should be valid Mermaid code, with no extra commentary or text beyond the code itself.
"""

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

# Helper Functions
def replace_special_statements(text):
    pattern = r'(\|\s*([^\|]+)\s*\|)|(\[\s*([^\]]+)\s*\])|(\{\s*([^\}]+)\s*\})'

    def replace_func(match):
        if match.group(1):  # If the match is within | |
            content = match.group(2)
        elif match.group(3):  # If the match is within [ ]
            content = match.group(4)
        else:  # If the match is within { }
            content = match.group(6)
        
        cleaned_content = ''.join(word.capitalize() for word in re.findall(r'\w+', content))
        
        if match.group(1):  # Replace | |
            return f"|{cleaned_content}|"
        elif match.group(3):  # Replace [ ]
            return f"[{cleaned_content}]"
        else:  # Replace { }  
            return f"{{{cleaned_content}}}"
    
    return re.sub(pattern, replace_func, text)

def generate_unique_filename(base_name: str, extension: str) -> str:
    """Generate a unique filename with timestamp and unique ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    safe_base_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)  # Make the base name safe for filenames
    return f"{safe_base_name}_{timestamp}_{unique_id}.{extension}"

def init_cache() -> shelve.Shelf:
    """Initialize the shelve cache."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    return shelve.open(os.path.join(CACHE_DIR, 'llm_cache.db'))

def generate_cache_key(prompt: str, model: str) -> str:
    """Generate a unique hash for cache key based on input."""
    key_string = f"{model}_{prompt}"
    return md5(key_string.encode()).hexdigest()

def generate_response_with_ollama(prompt: str, model: str) -> str:
    """Call the LLM via Ollama to generate responses with caching."""
    cache = init_cache()
    cache_key = generate_cache_key(prompt, model)

    # Check if the result is already cached
    if cache_key in cache:
        logging.info(f"Fetching result from cache for prompt: {prompt[:50]}...")
        response_content = cache[cache_key]
        cache.close()
        return response_content

    try:
        logging.debug(f"Sending request to Ollama with model '{model}' and prompt size {len(prompt)}")
        url = OLLAMA_URL
        payload = {"model": model, "prompt": prompt}
        headers = {'Content-Type': 'application/json'}

        # Send the request
        response = requests.post(url, data=json.dumps(payload), headers=headers, stream=True)

        if response.status_code != 200:
            logging.error(f"Failed to generate response with Ollama: HTTP {response.status_code}")
            cache.close()
            return ""

        response_content = ''
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
        logging.error(f"Failed to generate response with Ollama: {e}")
        logging.debug(f"Prompt used: {prompt[:200]}...")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        cache.close()
        raise e

def extract_mermaid_code(content: str) -> str:
    """Extract Mermaid code from LLM output."""
    lines = content.strip().splitlines()

    # Remove leading and trailing ```
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()

def generate_mermaid_code(combined_summary: str, mermaid_context: str) -> str:
    """Generate the Mermaid code based on the combined summary."""
    llm_mermaid_prompt = mermaid_context.format(combined_summary=combined_summary)

    # Save the Mermaid prompt context to a file for debugging
    save_output_to_file(llm_mermaid_prompt, MERMAID_PROMPT_FILE)

    # Generate Mermaid code
    mermaid_code = generate_response_with_ollama(llm_mermaid_prompt, DEFAULT_SUMMARIZATION_MODEL)

    # Extract Mermaid code from the response
    mermaid_code = extract_mermaid_code(mermaid_code)

    # Save the Mermaid code to a file
    mermaid_file = os.path.join(OUTPUT_DIR, "architecture_diagram.mmd")
    save_output_to_file(mermaid_code, mermaid_file)

    logging.info(f"Mermaid diagram generated and saved to {mermaid_file}")

    return mermaid_code

def summarize_codebase(directory: str, summarization_model: str) -> str:
    """Summarize the entire repository."""
    all_files = list_all_files(directory)
    total_files = len(all_files)
    codebase_summary = []
    logging.info(f"Total files to process: {total_files}")

    # Create OUTPUT_DIR and subdirectories
    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    os.makedirs(UNPROCESSED_DIR, exist_ok=True)

    for idx, file_path in enumerate(all_files, start=1):
        logging.info(f"Processing file {idx}/{total_files}: {file_path}")
        file_content = read_file(file_path, directory, UNPROCESSED_DIR)

        if not file_content:
            logging.warning(f"Skipping unreadable or empty file: {file_path}")
            continue

        try:
            summary, is_test_file_flag = generate_summary(file_path, file_content, summarization_model)

            if is_test_file_flag:
                logging.info(f"Test or irrelevant file detected and skipped: {file_path}")
                continue

            if summary:
                cleaned_summary = clean_generated_summary(summary)
                formatted_summary = f"File: {file_path}\n\n{cleaned_summary}\n"

                # Generate a safe filename for the summary
                file_summary_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', os.path.basename(file_path)) + "_summary.txt"

                # Treat all summaries as relevant and save to SUMMARIES_DIR
                codebase_summary.append(formatted_summary)
                save_output_to_file(formatted_summary, os.path.join(SUMMARIES_DIR, file_summary_name))

            if idx % 5 == 0 or idx == total_files:
                logging.info(f"Progress: {idx}/{total_files} files processed.")

        except Exception as e:
            logging.error(f"Error processing file: {file_path}")
            logging.error(f"Exception details: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")

            copy_unreadable_file(file_path, directory, UNPROCESSED_DIR)

    combined_summary = "\n".join(codebase_summary)

    if combined_summary:
        logging.info("Final codebase summary generated.")
        summary_file = os.path.join(OUTPUT_DIR, "codebase_summary.txt")
        save_output_to_file(combined_summary, summary_file)
    else:
        logging.warning("No relevant summaries generated.")

    return combined_summary

def generate_summary(file_path: str, file_content: str, summarization_model: str) -> tuple:
    """Generate a summary for each file."""
    if is_test_file(file_path):
        logging.info(f"Skipping test file: {file_path}")
        return None, True

    if len(file_content.strip()) == 0:
        logging.warning(f"Skipping empty file: {file_path}")
        return None, True

    # Prepare the prompt
    prompt = FILE_SUMMARY_PROMPT_TEMPLATE.format(
        file_path=file_path,
        file_content=file_content
    )

    # Generate the summary
    summary = generate_response_with_ollama(prompt, summarization_model)
    return clean_generated_summary(summary), False

def clean_generated_summary(summary: str) -> str:
    """Clean and format the final summary."""
    cleaned_summary = "\n".join(
        [sentence for sentence in summary.split("\n") if not sentence.startswith("Let me know")]
    )
    return cleaned_summary.rstrip()

def read_file(file_path: str, base_directory: str, unprocessed_directory: str) -> str:
    """Read the contents of a file using the appropriate reader module."""
    try:
        _, file_extension = os.path.splitext(file_path)
        reader = get_reader(file_extension)
        return reader(file_path)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        copy_unreadable_file(file_path, base_directory, unprocessed_directory)
        return ""

def save_output_to_file(content: str, file_name: str):
    """Save output to a file."""
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(content)

def list_all_files(directory: str) -> list:
    """List all relevant files in the directory."""
    all_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if is_relevant_file(file_path):
                all_files.append(file_path)
    return all_files

def copy_unreadable_file(file_path: str, base_directory: str, unprocessed_directory: str):
    """Copy unreadable files to a new directory while maintaining relative paths."""
    relative_path = os.path.relpath(file_path, base_directory)
    dest_path = os.path.join(unprocessed_directory, relative_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(file_path, dest_path)
    logging.info(f"Copied unreadable file {file_path} to {dest_path}")

def is_test_file(file_path: str) -> bool:
    """Determine if the file is a test file."""
    file_path_lower = file_path.lower()
    test_indicators = [
        "src/it",
        "src/performance",
        "src/ct",
        "src/test",
        "test/resources",
        "test/java",
        "test",
        "/tests/",
        "\\tests\\",
        "/test/",
        "\\test\\",
        "test_",
        "_test",
        "spec/",
        "spec\\",
        "specs/",
        "specs\\",
        "/spec/",
        "\\spec\\",
    ]
    for indicator in test_indicators:
        if indicator in file_path_lower:
            return True

    return False

def is_relevant_file(file_path: str) -> bool:
    """Determine if a file is relevant to process."""
    # Exclude test files
    if is_test_file(file_path):
        return False
    # Exclude specific files
    EXCLUDED_FILES = [
        'pom.xml', 'jenkinsfile', 'build.gradle', 'package.json', 'package-lock.json',
        'yarn.lock', 'Makefile', 'Dockerfile', 'README.md', 'LICENSE', 'CONTRIBUTING.md',
        '.gitignore', 'gradlew', 'gradlew.bat', 'mvnw', 'mvnw.cmd', 'setup.py',
        'requirements.txt', 'environment.yml', 'Pipfile', 'Pipfile.lock', 'Gemfile', 
        'Gemfile.lock', '.gitlab-ci.yml', 'renovate.json', 'Dockerfile', 'docker-compose.yml',
        'bootstrap.min.css'
    ]
    if os.path.basename(file_path).lower() in EXCLUDED_FILES:
        return False
    # Include files with relevant extensions
    RELEVANT_EXTENSIONS = [
        '.java', '.kt', '.xml', '.yml', '.yaml', '.properties', '.conf', '.sql', '.json',
        '.js', '.ts', '.tsx', '.jsx', '.py', '.rb', '.go', '.php', '.cs', '.cpp', '.c',
        '.h', '.swift', '.rs', '.erl', '.ex', '.exs', '.html', '.htm', '.txt', '.md', '.docx', '.pdf'
    ]
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() in RELEVANT_EXTENSIONS:
        return True
    return False

def main():
    # Define constants for the directory and models
    directory = 'repo'  # Change to your repository path
    summarization_model = DEFAULT_SUMMARIZATION_MODEL
    mermaid_context = DEFAULT_MERMAID_PROMPT_TEMPLATE

    # Run summarization
    codebase_summary = summarize_codebase(
        directory,
        summarization_model
    )

    if codebase_summary:
        # Generate Mermaid code
        generate_mermaid_code(
            codebase_summary,
            mermaid_context
        )
    else:
        logging.warning("No files found or summarized.")

if __name__ == "__main__":
    main()
