import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from trafilatura import fetch_url, extract
from tqdm import tqdm

OUTPUT_DIR = "output/raw"
CRAWL_LIMIT = 300      # pages per domain
DELAY = 2              # seconds

os.makedirs(OUTPUT_DIR, exist_ok=True)
visited = set()
domain_count = {}

def clean_text(text):
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]
    return "\n".join(lines)

def extract_links(url, soup):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(url, href)
        if full.startswith("http"):
            links.add(full.split("#")[0])
    return links

def allowed(url):
    domain = urlparse(url).netloc
    domain_count.setdefault(domain, 0)
    if domain_count[domain] >= CRAWL_LIMIT:
        return False
    domain_count[domain] += 1
    return True

def scrape_url(url):
    if url in visited or not allowed(url):
        return None

    visited.add(url)

    downloaded = fetch_url(url)
    if not downloaded:
        return None

    text = extract(downloaded)
    if not text or len(text) < 800:
        return None

    return clean_text(text)

def crawl(start_urls):
    queue = list(start_urls)

    for url in tqdm(queue):
        try:
            text = scrape_url(url)
            if text:
                fname = f"{len(visited)}.json"
                with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as f:
                    json.dump({
                        "url": url,
                        "text": text
                    }, f, ensure_ascii=False, indent=2)

                # crawl deeper
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "lxml")
                links = extract_links(url, soup)
                for l in links:
                    if l not in visited:
                        queue.append(l)

            time.sleep(DELAY)

        except Exception:
            continue

if __name__ == "__main__":
    with open("sources.txt") as f:
        urls = [l.strip() for l in f if l.strip()]
    crawl(urls)
