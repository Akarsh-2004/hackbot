import os
import json
import fitz  # pymupdf
import markdown
from bs4 import BeautifulSoup
from tqdm import tqdm

BOOKS_DIR = "Books"
OUTPUT = "data/processed/book_raw.jsonl"

os.makedirs("data/processed", exist_ok=True)

def extract_pdf(path):
    doc = fitz.open(path)
    text = []
    for page in doc:
        t = page.get_text()
        if len(t) > 200:
            text.append(t)
    return "\n".join(text)

def extract_md(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        html = markdown.markdown(f.read())
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text("\n")

def clean(text):
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 50]
    return "\n".join(lines)

with open(OUTPUT, "w", encoding="utf-8") as out:
    for root, _, files in os.walk(BOOKS_DIR):
        for file in tqdm(files):
            path = os.path.join(root, file)
            try:
                if file.lower().endswith(".pdf"):
                    text = extract_pdf(path)
                elif file.lower().endswith(".md"):
                    text = extract_md(path)
                else:
                    continue

                text = clean(text)
                if len(text) < 1000:
                    continue

                out.write(json.dumps({
                    "source": "book",
                    "book": os.path.basename(root),
                    "file": file,
                    "text": text
                }) + "\n")

            except Exception:
                continue
