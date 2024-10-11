from pathlib import Path
import re
import uuid
from datetime import datetime

def generate_unique_filename(base_name: str, extension: str) -> str:
    """Generate a unique filename with timestamp and unique ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    safe_base_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
    return f"{safe_base_name}_{timestamp}_{unique_id}.{extension}"

def save_output_to_file(content: str, file_path: Path):
    """Save output to a file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)