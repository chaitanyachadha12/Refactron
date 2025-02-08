"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import subprocess
import os

class ToolIntegration:
    """
    ToolIntegration class to integrate and run supporting tools like linters, test runners,
    and to generate code diffs.
    """

    def __init__(self):
        pass

    def run_linter(self, file_path: str) -> str:
        """
        Run a linter (flake8) on the specified file.
        If the file is not a Python file, return an appropriate message.
        :param file_path: Path to the file to lint.
        :return: Linter output or error message.
        """
        if not file_path.lower().endswith('.py'):
            return f"Skipping linting: {os.path.basename(file_path)} is not a Python file."
        try:
            result = subprocess.run(
                ["flake8", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return result.stdout + result.stderr
            return "No linting issues found."
        except subprocess.TimeoutExpired:
            return "Linter execution timed out."
        except FileNotFoundError:
            return "Linter tool not found. Please install flake8."
        except Exception as e:
            return f"Error running linter: {e}"

    def run_tests(self, test_directory: str) -> str:
        """
        Run tests using pytest in the specified directory.
        :param test_directory: Directory in which to run pytest.
        :return: Test results output or error message.
        """
        try:
            result = subprocess.run(
                ["pytest", "--maxfail=1", "--disable-warnings", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=test_directory  # Change working directory to the repository path.
            )
            if result.returncode != 0:
                return result.stdout + result.stderr
            return "All tests passed successfully."
        except subprocess.TimeoutExpired:
            return "Test execution timed out."
        except FileNotFoundError:
            return "Test runner not found. Please install pytest."
        except Exception as e:
            return f"Error running tests: {e}"

    def generate_diff(self, original: str, modified: str) -> str:
        """
        Generate a unified diff between the original and modified code.
        :param original: The original code string.
        :param modified: The modified code string.
        :return: A unified diff as a string.
        """
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="Original",
            tofile="Modified"
        )
        return ''.join(diff)
