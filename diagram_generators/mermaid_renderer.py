import os
from pathlib import Path
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from helpers import generate_unique_filename
from .base_renderer import BaseRenderer

class MermaidRenderer(BaseRenderer):
    """Renderer for Mermaid diagrams."""

    def generate_png(self, diagram_code: str, output_dir: Path) -> Path:
        """Generate a PNG image from Mermaid code with enhanced error handling and syntax checks."""
        # Prepare the diagram code for embedding in JavaScript
        diagram_code_js = json.dumps(diagram_code)  # Properly escape diagram_code for JavaScript string literal

        # Define the HTML template with Mermaid.js and enhanced error handling
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Mermaid Diagram</title>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

                window.onload = function() {{
                    try {{
                        // Check if the diagram has valid syntax
                        mermaid.parse({diagram_code_js});

                        // Initialize Mermaid
                        mermaid.initialize({{ startOnLoad: true }});

                    }} catch (error) {{
                        document.getElementById('mermaid-error').textContent = error.message;
                    }}
                }};
            </script>
        </head>
        <body>
            <div class="mermaid">
{diagram_code}
            </div>
            <div id="mermaid-error" style="color: red; font-weight: bold;"></div>
        </body>
        </html>
        """

        # Save the HTML to a temporary file
        temp_html_file = output_dir / 'temp_mermaid_diagram.html'
        with open(temp_html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        # Configure Selenium to use headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Automatically install the correct version of ChromeDriver using webdriver-manager
        driver_service = Service(ChromeDriverManager().install())

        # Initialize the WebDriver
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)

        try:
            # Load the HTML file
            driver.get(f'file://{temp_html_file.absolute()}')

            # Give Mermaid some time to render the diagram
            time.sleep(3)

            # Capture console logs to detect JavaScript errors (like Mermaid parsing issues)
            logs = driver.get_log("browser")
            has_severe_error = False
            error_messages = []

            for log_entry in logs:
                logging.warning(f"Browser log: {log_entry}")
                if log_entry['level'] == 'SEVERE':
                    has_severe_error = True
                    error_messages.append(log_entry['message'])

            if has_severe_error:
                combined_error_message = "\n".join(error_messages)
                logging.error(f"Mermaid rendering or syntax error detected: {combined_error_message}")
                raise Exception(f"Mermaid rendering or syntax error: {combined_error_message}")

            # Check if the diagram element exists
            try:
                diagram_element = driver.find_element("class name", 'mermaid')
            except Exception as e:
                logging.error(f"Diagram element not found: {e}")
                raise Exception("Mermaid diagram element not found; possible rendering error.")

            png_filename = generate_unique_filename("mermaid_diagram", "png")
            png_filepath = output_dir / png_filename

            # Save screenshot of the element
            diagram_element.screenshot(str(png_filepath))

            logging.info(f"Mermaid diagram image saved to {png_filepath}")

        except Exception as e:
            logging.error(f"Error generating PNG from Mermaid code: {e}")
            png_filepath = None
            raise e  # Re-raise the exception to let the caller handle it

        finally:
            driver.quit()

            # Remove the temporary HTML file
            if temp_html_file.exists():
                temp_html_file.unlink()

        return png_filepath