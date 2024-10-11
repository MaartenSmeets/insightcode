from pathlib import Path

# Constants and Configuration
OUTPUT_FORMAT = 'mermaid'  # Can be 'mermaid', 'plantuml', etc.

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"  # Configurable LLM URL
DEFAULT_SUMMARIZATION_MODEL = 'llama3.1:8b-instruct-fp16'  # Configurable model

# Directories
CACHE_DIR = Path('cache')
OUTPUT_DIR = Path('output')

# Subdirectories within OUTPUT_DIR
SUMMARIES_DIR = OUTPUT_DIR / "summaries"
UNPROCESSED_DIR = OUTPUT_DIR / "unprocessed_files"