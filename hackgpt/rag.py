import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from functools import lru_cache

DATA_DIR = "data"
CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.jsonl")
INDEX_FILE = os.path.join(DATA_DIR, "index.faiss")
MODEL_NAME = "all-MiniLM-L6-v2"

class RAGEngine:
    def __init__(self):
        print("[*] Loading RAG engine...")
        if not os.path.exists(INDEX_FILE) or not os.path.exists(CHUNKS_FILE):
             raise FileNotFoundError("Index or chunks not found. Run ingest.py first.")
             
        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(INDEX_FILE)
        
        self.chunks = []
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                self.chunks.append(json.loads(line))
        print("[+] RAG engine loaded.")

    @lru_cache(maxsize=100)
    def _encode_cached(self, query):
        """Cache embeddings for repeated queries"""
        return tuple(self.model.encode([query])[0])

    def retrieve(self, query, k=3):
        """Retrieve top-k chunks with similarity scores"""
        # Use cached encoding
        q_emb_tuple = self._encode_cached(query)
        q_emb = np.array([list(q_emb_tuple)])
        
        distances, indices = self.index.search(q_emb, k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                # Convert L2 distance to similarity score (lower is better)
                chunk['similarity_score'] = float(1 / (1 + dist))
                results.append(chunk)
                
        return results

if __name__ == "__main__":
    # Test
    rag = RAGEngine()
    res = rag.retrieve("smb port 445")
    for r in res:
        print("-" * 50)
        print(f"Score: {r['similarity_score']:.3f}")
        print(r["text"][:200] + "...")

