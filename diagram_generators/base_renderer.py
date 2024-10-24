from pathlib import Path
from abc import ABC, abstractmethod

class BaseRenderer(ABC):
    """Abstract base class for diagram renderers."""

    @abstractmethod
    def generate_png(self, diagram_code: str, output_dir: Path) -> Path:
        """Generate a PNG from the diagram code."""
        pass