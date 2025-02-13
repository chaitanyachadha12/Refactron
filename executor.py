"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import subprocess
import tempfile
import os

def run_in_sandbox(code: str, timeout: int = 5) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name
    try:
        result = subprocess.run(
            ["python", tmp_file_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = "Code execution timed out."
    finally:
        os.remove(tmp_file_path)
    return output
