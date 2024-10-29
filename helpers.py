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

def is_irrelevant_file(file_path: Path) -> bool:
    """Determine if a file should be excluded from analysis."""
    # Define the maximum file size (in bytes) for source code files
    MAX_FILE_SIZE = 500 * 1024  # 500KB

    # List of irrelevant file extensions
    irrelevant_extensions = [
        # Compiled and binary files
        '.bin', '.exe', '.o', '.obj', '.class', '.pyc', '.pyo', '.jar', '.war', '.ear', '.dll', '.so', '.dylib',
        '.lib', '.a', '.whl', '.apk', '.ipa',
        # Image and media files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico',
        '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm',
        # Documentation and miscellaneous files
        '.rst', '.csv', '.tsv', '.log', '.feature', '.xls', '.xlsx', '.odt', '.odp', '.rtf',
        # Archive and package files
        '.zip', '.tar', '.gz', '.tar.gz', '.tgz', '.rar', '.7z', '.bz2', '.xz', '.egg', '.gem', '.deb', '.rpm',
        # Other non-source code files
        '.swp', '.swo', '.tmp', '.cache', '.pyproj', '.csproj', '.sln', '.vcxproj',
        # Spring and Java-related irrelevant files
        '.iml', '.bak',  # IntelliJ IDEA files
    ]

    # List of irrelevant directories
    irrelevant_directories = [
        # Test directories
        'test', 'tests', 'spec', 'specs', 'mock', 'mocks', 'stub', 'stubs', 'fixtures', 'benchmark', 'benchmarks', 'ct', 'it', 'performance'
        # Version control and IDE directories
        '.git', '.svn', '.hg', '.idea', '.vscode', '__pycache__', '.tox', '.pytest_cache',
        # Build and dependency directories
        'build', 'dist', 'node_modules', 'env', 'venv', 'target', 'out', 'bin', 'obj', 'lib', 'libs',
        'generated', 'gen', 'public', 'private', 'release', 'debug', 'bower_components',
        # CI/CD and deployment directories
        '.circleci', '.github', '.gitlab', '.azure', '.vagrant', '.docker', '.dockerignore',
        # Coverage and report directories
        'coverage', 'reports', 'logs',
    ]

    # List of irrelevant filenames
    irrelevant_filenames = [
        # Common non-code files
        'LICENSE', 'LICENSE.txt', 'README', 'README.md', 'README.txt', 'CHANGES', 'CHANGELOG',
        'CONTRIBUTING', 'CODE_OF_CONDUCT', '.gitignore', '.gitattributes', 'Dockerfile',
        'Makefile', 'CMakeLists.txt', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
        # Maven wrapper
        'mvnw', 'mvnw.cmd',
        # Gradle wrapper
        'gradlew', 'gradlew.bat',
    ]

    # Check for irrelevant file extensions
    if file_path.suffix.lower() in irrelevant_extensions:
        return True

    # Check if the file is in an irrelevant directory
    if any(dir_name.lower() == part.lower() for dir_name in irrelevant_directories for part in file_path.parts):
        return True

    # Check for irrelevant filenames
    if file_path.name in irrelevant_filenames:
        return True

    # Exclude large files (e.g., files larger than 500KB)
    if file_path.is_file() and file_path.stat().st_size > MAX_FILE_SIZE:
        return True

    # Exclude build files commonly found in various languages and frameworks
    build_files = [
        # Java and related build files
        'pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle', 'settings.gradle.kts',
        'gradlew', 'gradlew.bat', 'mvnw', 'mvnw.cmd', '.gitignore','.gitattributes','.prettierrc','.prettierignore','.editorconfig',
        # .NET build files
        '*.csproj', '*.vbproj', '*.fsproj', '*.sln',
        # JavaScript and TypeScript build files
        'gulpfile.js', 'gulpfile.ts', 'Gruntfile.js', 'Gruntfile.ts', 'webpack.config.js',
        'webpack.config.ts', 'rollup.config.js', 'rollup.config.ts', 'vite.config.js', 'vite.config.ts',
        # Python build files
        'setup.py', 'setup.cfg', 'pyproject.toml', 'requirements.txt', 'Pipfile', 'Pipfile.lock',
        # Ruby build files
        'Gemfile', 'Gemfile.lock', 'Rakefile',
        # PHP build files
        'composer.json', 'composer.lock',
        # Go build files
        'go.mod', 'go.sum',
        # Rust build files
        'Cargo.toml', 'Cargo.lock',
        # Spring and Spring Boot build files
        'application.properties', 'application.yml', 'application.yaml',
        'logback.xml',  # Logging config for Spring Boot
    ]

    # Check for build files
    if file_path.name.lower() in [name.lower() for name in build_files]:
        return True

    # Exclude generated files (e.g., package-lock.json)
    generated_files = [
        'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    ]
    if file_path.name.lower() in [name.lower() for name in generated_files]:
        return True

    return False