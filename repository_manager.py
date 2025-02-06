"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gwu.edu
Created on: 02-06-2025
Updated on: 
"""

import os
import git 
from typing import List, Dict, Any

class RepositoryManager:
    """
    RepositoryManager class to scan the repository and extract code context.
    Handles file I/O, error handling, and chunking for large files.
    """

    def __init__(self, repo_path: str):
        """
        Initialize with the repository path.
        :param repo_path: The path to the Git repository.
        """
        self.repo_path = repo_path
        self.repo = None

    def load_repository(self) -> bool:
        """
        Load the repository using GitPython.
        :return: True if successful, False otherwise.
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
        :return: List of file paths.
        """
        file_paths = []
        try:
            for root, _, files in os.walk(self.repo_path):
                for file in files:
                    # Skip hidden files 
                    if not file.startswith('.'):
                        file_paths.append(os.path.join(root, file))
            return file_paths
        except Exception as e:
            print(f"Error while scanning repository: {e}")
            return []

    def read_file(self, file_path: str) -> str:
        """
        Read a file and return its content.
        :param file_path: The file path to read.
        :return: Content of the file, or an empty string in case of error.
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
        For small files, return the full content; for larger files, split into chunks.
        :param max_chunk_size: Maximum number of characters per chunk.
        :return: A list of dictionaries with keys 'file', 'content', and optional 'chunk_index'.
        """
        chunks = []
        files = self.get_all_files()
        for file in files:
            content = self.read_file(file)
            if content:
                # If the file's content is within the size limit, add it as one chunk.
                if len(content) <= max_chunk_size:
                    chunks.append({"file": file, "content": content})
                else:
                    # Split the content into smaller chunks.
                    for i in range(0, len(content), max_chunk_size):
                        chunk_content = content[i:i+max_chunk_size]
                        chunks.append({
                            "file": file,
                            "content": chunk_content,
                            "chunk_index": i // max_chunk_size
                        })
        return chunks
