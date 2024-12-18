# File: config.py

from pathlib import Path

# Constants and Configuration
OUTPUT_FORMAT = 'mermaid'  # Can be 'mermaid', 'plantuml', etc.

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"  # Configurable LLM URL
DEFAULT_SUMMARIZATION_MODEL = "deepseek-coder-v2:16b-lite-instruct-q5_K_M"  # Configurable model. This works on 16Gb NVidia or CPU 32Gb RAM
DEFAULT_DIAGRAM_MODEL = "deepseek-coder-v2:236b-instruct-q3_K_M"  # Configurable model. This works on 16Gb VRAM Nvidia + 64Gb CPU RAM
CLEAN_CACHE_ON_STARTUP = False  # Set to True to clean cache at startup, False to retain cache

# Diagram Generation Configuration
GENERATE_DIAGRAM = False  # Set to True to enable diagram generation, False to disable
MAX_FIX_ATTEMPTS = 2  # Maximum number of attempts to fix the diagram code

# Directories
CACHE_DIR = Path('cache')
OUTPUT_DIR = Path('output')

# Subdirectories within OUTPUT_DIR
SUMMARIES_DIR = OUTPUT_DIR / "summaries"
UNPROCESSED_DIR = OUTPUT_DIR / "unprocessed_files"
