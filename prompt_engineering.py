"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

from typing import List, Dict

class PromptEngineer:
    """
    PromptEngineer class to build prompts by merging user queries with code context.
    Currently, it concatenates a few code chunks; later, a retrieval system can be integrated.
    """

    def __init__(self):
        pass

    def build_prompt(self, query: str, code_chunks: List[Dict[str, str]]) -> str:
        """
        Build a prompt by combining the user's query with relevant code chunks.
        :param query: The user's query.
        :param code_chunks: A list of dictionaries, each containing 'file' and 'content' keys.
        :return: A string prompt ready to be sent to the LLM.
        """
        prompt = f"User Query: {query}\n\n"
        prompt += "Code Context:\n"
        # For simplicity, we select the first 3 chunks.
        # Future implementation: use a retrieval system to select the most relevant chunks.
        for chunk in code_chunks[:3]:
            file = chunk.get("file", "unknown")
            content = chunk.get("content", "")
            prompt += f"\n--- File: {file} ---\n{content}\n"
        return prompt
