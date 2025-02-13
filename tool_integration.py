"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import subprocess
import os
import difflib

class ToolIntegration:
    def __init__(self):
        pass

    def run_linter(self, file_path: str) -> str:
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
        try:
            result = subprocess.run(
                ["pytest", "--maxfail=1", "--disable-warnings", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=test_directory
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
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="Original",
            tofile="Modified"
        )
        return ''.join(diff)

    def apply_lint_suggestions(self, file_path: str) -> str:
        try:
            result = subprocess.run(
                ["autopep8", "--in-place", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return f"Error applying lint suggestions: {result.stdout} {result.stderr}"
            return "Lint suggestions applied successfully."
        except subprocess.TimeoutExpired:
            return "Auto-fix execution timed out."
        except FileNotFoundError:
            return "Auto-fix tool not found. Please install autopep8."
        except Exception as e:
            return f"Error applying lint suggestions: {e}"
