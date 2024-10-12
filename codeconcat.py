import os

def combine_python_files(folder_path, output_file, exclude_folders=None):
    """
    Combines all Python files in the specified folder and its subfolders into a single file.
    The relative path of each file is added before its content.
    Folders specified in exclude_folders will be skipped.

    Args:
    folder_path (str): Path to the folder containing the Python files.
    output_file (str): Path to the output file where the combined content will be saved.
    exclude_folders (list, optional): List of folder names to exclude from the search.
                                      Defaults to excluding '.venv'.
    """

    # Set default excluded folders if none provided
    if exclude_folders is None:
        exclude_folders = ['.venv', '__pycache__', '.git', '.idea', 'repo']

    with open(output_file, 'w') as outfile:
        # Walk through the folder and subfolders
        for root, dirs, files in os.walk(folder_path):
            # Skip excluded folders
            dirs[:] = [d for d in dirs if d not in exclude_folders]

            for file in files:
                if file.endswith(".py"):
                    # Get the relative path of the file
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, folder_path)

                    # Write the relative path to the output file
                    outfile.write(f"# File: {relative_path}\n\n")

                    # Write the content of the file to the output file
                    with open(file_path, 'r') as infile:
                        content = infile.read()
                        outfile.write(content)

                    # Add a separator between files
                    outfile.write("\n\n" + "="*80 + "\n\n")

    print(f"All Python files from '{folder_path}' have been combined into '{output_file}'.")


# Example usage:
folder_path = './.'  # Change this to your target folder
output_file = './combined_python_files.txt'  # Change this to the desired output file path
exclude_folders = ['.venv', '__pycache__']  # Add more folders to exclude if needed
combine_python_files(folder_path, output_file, exclude_folders)
