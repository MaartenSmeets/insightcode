import os
import logging
from pathlib import Path
from plantuml import PlantUML, PlantUMLHTTPError
from helpers import generate_unique_filename
from .base_renderer import BaseRenderer

class PlantUMLRenderer(BaseRenderer):
    """Renderer for PlantUML diagrams."""

    def generate_png(self, diagram_code: str, output_dir: Path) -> Path:
        """Generate a PNG image from PlantUML code using the public PlantUML server."""
        # Create a unique filename for the output image
        png_filename = generate_unique_filename("plantuml_diagram", "png")
        png_filepath = output_dir / png_filename

        # Create a PlantUML client pointing to the public server
        plantuml_server = PlantUML(url='http://www.plantuml.com/plantuml/img/')

        try:
            # Get the PNG image bytes
            png_data = plantuml_server.processes(diagram_code)

            # Write the PNG data to a file
            with open(png_filepath, 'wb') as f:
                f.write(png_data)

            logging.info(f"PlantUML diagram image saved to {png_filepath}")

        except PlantUMLHTTPError as e:
            logging.error(f"Error generating PNG from PlantUML code: {e}")
            raise e  # Re-raise the exception to let the caller handle it

        return png_filepath
