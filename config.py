from pathlib import Path

# Constants and Configuration
OUTPUT_FORMAT = 'mermaid'  # Can be 'mermaid', 'plantuml', etc.

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"  # Configurable LLM URL
DEFAULT_SUMMARIZATION_MODEL = "deepseek-coder-v2:16b-lite-instruct-q5_K_M"  # Configurable model
DEFAULT_DIAGRAM_MODEL = "llama3.1:70b-instruct-q4_K_M"  # Configurable model
CLEAN_CACHE_ON_STARTUP = False  # Set to True to clean cache at startup, False to retain cache

# Diagram Generation Configuration
GENERATE_DIAGRAM = False  # Set to True to enable diagram generation, False to disable

# Directories
CACHE_DIR = Path('cache')
OUTPUT_DIR = Path('output')

# Subdirectories within OUTPUT_DIR
SUMMARIES_DIR = OUTPUT_DIR / "summaries"
UNPROCESSED_DIR = OUTPUT_DIR / "unprocessed_files"
