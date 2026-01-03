import os
import json
import glob
import subprocess
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import faiss

# Paths
DATA_DIR = "data"
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
WALKTHROUGHS_DIR = os.path.join(DATA_DIR, "walkthroughs")
RAW_WEB_DIR = "output/raw"
CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.jsonl")
INDEX_FILE = os.path.join(DATA_DIR, "index.faiss")

# Model
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
OVERLAP = 50

def run_scrapers():
    print("[*] Running scrapers/processors...")
    
    # Run book scraper
    if os.path.exists("book_scrapper.py"):
        print("   - Running book_scrapper.py (this might take a while)...")
        subprocess.run(["python", "book_scrapper.py"], check=False)
    else:
        print("   [!] book_scrapper.py not found.")
        
    # Run github scraper
    if os.path.exists("hackgpt/github_scraper.py"):
        print("   - Running github_scraper.py...")
        subprocess.run(["python", "hackgpt/github_scraper.py"], check=False)
    else:
        print("   [!] hackgpt/github_scraper.py not found.")

def chunk_text(text, source_meta):
    """
    Splits text into chunks and returns a list of dictionaries with metadata.
    """
    if not text:
        return []
        
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), CHUNK_SIZE - OVERLAP):
        chunk_words = words[i:i + CHUNK_SIZE]
        chunk_text = " ".join(chunk_words)
        
        if len(chunk_text) < 50:  # Skip tiny chunks
            continue
            
        chunks.append({
            "text": chunk_text,
            **source_meta
        })
    return chunks

def load_and_chunk_data():
    all_chunks = []
    
    # 1. Process Books
    book_file = "data/processed/book_raw.jsonl"
    if os.path.exists(book_file):
        print("[*] Processing Books...")
        with open(book_file, "r", encoding="utf-8") as f:
            for line in tqdm(f):
                try:
                    data = json.loads(line)
                    meta = {"source": "book", "title": data.get("book", "unknown"), "file": data.get("file", "unknown")}
                    all_chunks.extend(chunk_text(data.get("text", ""), meta))
                except json.JSONDecodeError:
                    continue
    else:
        print(f"[!] {book_file} not found. Skipping books.")

    # 2. Process Web Scraped Data
    if os.path.exists(RAW_WEB_DIR):
        print("[*] Processing Scraped Web Data...")
        files = glob.glob(os.path.join(RAW_WEB_DIR, "*.json"))
        for fpath in tqdm(files):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                    text = data.get("text", "")
                    url = data.get("url", "unknown")
                    meta = {"source": "web", "url": url}
                    all_chunks.extend(chunk_text(text, meta))
            except Exception:
                continue

    # 3. Process GitHub Walkthroughs
    if os.path.exists(WALKTHROUGHS_DIR):
        print("[*] Processing Walkthroughs...")
        for root, _, files in os.walk(WALKTHROUGHS_DIR):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                            # Basic cleanup
                            rel_path = os.path.relpath(path, WALKTHROUGHS_DIR)
                            meta = {"source": "walkthrough", "path": rel_path}
                            all_chunks.extend(chunk_text(text, meta))
                    except Exception:
                        continue

    return all_chunks

def create_index(chunks):
    if not chunks:
        print("[!] No chunks to index.")
        return

    print(f"[*] Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    print("[*] Encoding chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print("[*] Creating FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    
    # Save
    faiss.write_index(index, INDEX_FILE)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")
            
    print(f"[+] Index saved to {INDEX_FILE}")
    print(f"[+] Chunks saved to {CHUNKS_FILE}")

def main():
    run_scrapers()
    chunks = load_and_chunk_data()
    print(f"[*] Total chunks generated: {len(chunks)}")
    create_index(chunks)

if __name__ == "__main__":
    main()
