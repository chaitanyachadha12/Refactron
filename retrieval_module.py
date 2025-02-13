"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class RetrievalModule:
    def __init__(self, embedding_dim: int = 384):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.chunk_mapping = []

    def embed_chunks(self, code_chunks):
        texts = [chunk["content"] for chunk in code_chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        self.index.reset()
        self.index.add(embeddings)
        self.chunk_mapping = code_chunks
        return embeddings

    def search(self, query: str, top_k: int = 3):
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        results = [self.chunk_mapping[idx] for idx in indices[0] if idx < len(self.chunk_mapping)]
        return results
