"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""
# repository_manager.py
import os
import time
import git  # Requires GitPython: pip install gitpython
from typing import List, Dict, Any
import ast

class RepositoryManager:
    """
    Scans the repository and extracts code context.
    Skips directories and files that are likely to contain non-text (binary) data.
    For Python files, it extracts function and class definitions as logical chunks.
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
        skip_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.exe', '.dll', '.so', '.bin'}
        try:
            for root, dirs, files in os.walk(self.repo_path):
                if any(excluded in root for excluded in ['.git', 'venv', '__pycache__']):
                    continue
                for file in files:
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
        - For Python files (.py), attempts to parse using the AST module and extract functions and classes.
        - For other files or in case of parsing errors, falls back to simple chunking.
        """
        chunks = []
        files = self.get_all_files()
        for file in files:
            content = self.read_file(file)
            if not content:
                continue

            file_size = len(content)
            modification_time = os.path.getmtime(file)
            ext = os.path.splitext(file)[1].lower()

            if ext == ".py":
                # Attempt to parse and extract functions and classes
                try:
                    tree = ast.parse(content, filename=file)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                                start = node.lineno - 1  # Convert to 0-indexed
                                end = node.end_lineno
                                lines = content.splitlines()
                                snippet = "\n".join(lines[start:end])
                                chunks.append({
                                    "file": file,
                                    "type": "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class",
                                    "name": node.name,
                                    "content": snippet,
                                    "modified": time.ctime(modification_time)
                                })
                except Exception as e:
                    print(f"Error parsing Python file {file}: {e}")
                    # Fall back to basic chunking if parsing fails
                    if file_size <= max_chunk_size:
                        chunks.append({
                            "file": file,
                            "content": content,
                            "modified": time.ctime(modification_time)
                        })
                    else:
                        for i in range(0, file_size, max_chunk_size):
                            chunk_content = content[i:i + max_chunk_size]
                            chunks.append({
                                "file": file,
                                "content": chunk_content,
                                "chunk_index": i // max_chunk_size,
                                "modified": time.ctime(modification_time)
                            })
            else:
                # For non-Python files, use basic chunking
                if file_size <= max_chunk_size:
                    chunks.append({
                        "file": file,
                        "content": content,
                        "modified": time.ctime(modification_time)
                    })
                else:
                    for i in range(0, file_size, max_chunk_size):
                        chunk_content = content[i:i + max_chunk_size]
                        chunks.append({
                            "file": file,
                            "content": chunk_content,
                            "chunk_index": i // max_chunk_size,
                            "modified": time.ctime(modification_time)
                        })
        return chunks
