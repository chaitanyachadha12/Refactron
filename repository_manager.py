"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

# repository_manager.py

import os
import git  # Requires GitPython: pip install gitpython
from typing import List, Dict, Any

class RepositoryManager:
    """
    Scans the repository and extracts code context.
    Skips directories and files that are likely to contain non-text (binary) data.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = None

    def load_repository(self) -> bool:
        """
        Load the repository using GitPython.
        """
        try:
            self.repo = git.Repo(self.repo_path)
            return True
        except git.exc.InvalidGitRepositoryError:
            print("Error: The provided path is not a valid Git repository.")
            return False
        except Exception as e:
            print(f"Error: Failed to load repository: {e}")
            return False

    def get_all_files(self) -> List[str]:
        """
        Recursively get all file paths in the repository.
        Skips directories such as '.git', 'venv', '__pycache__', and files with binary extensions.
        """
        file_paths = []
        # Set of file extensions to skip (you can add more if needed)
        skip_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.exe', '.dll', '.so', '.bin'}
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip directories that are not relevant
                if any(excluded in root for excluded in ['.git', 'venv', '__pycache__']):
                    continue
                for file in files:
                    # Skip hidden files
                    if file.startswith('.'):
                        continue
                    ext = os.path.splitext(file)[1].lower()
                    if ext in skip_extensions:
                        continue
                    file_paths.append(os.path.join(root, file))
            return file_paths
        except Exception as e:
            print(f"Error while scanning repository: {e}")
            return []

    def read_file(self, file_path: str) -> str:
        """
        Read a file as text.
        Returns an empty string if the file cannot be read.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

    def get_code_chunks(self, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Get code chunks from the repository.
        For small files, returns the full content; for larger files, splits into chunks.
        """
        chunks = []
        files = self.get_all_files()
        for file in files:
            content = self.read_file(file)
            if content:
                if len(content) <= max_chunk_size:
                    chunks.append({"file": file, "content": content})
                else:
                    # Split file content into chunks of up to max_chunk_size characters.
                    for i in range(0, len(content), max_chunk_size):
                        chunk_content = content[i:i + max_chunk_size]
                        chunks.append({
                            "file": file,
                            "content": chunk_content,
                            "chunk_index": i // max_chunk_size
                        })
        return chunks
