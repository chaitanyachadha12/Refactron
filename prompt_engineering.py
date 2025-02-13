"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

from typing import List, Dict
from retrieval_module import RetrievalModule

class PromptEngineer:
    def __init__(self):
        self.retrieval = RetrievalModule()

    def build_prompt(self, query: str, code_chunks: List[Dict[str, str]]) -> str:
        self.retrieval.embed_chunks(code_chunks)
        relevant_chunks = self.retrieval.search(query, top_k=3)
        prompt = f"User Query: {query}\n\nCode Context:\n"
        for chunk in relevant_chunks:
            file = chunk.get("file", "unknown")
            snippet = chunk.get("content", "")
            prompt += f"\n--- File: {file} ---\n{snippet}\n"
        return prompt
