import requests
import json

OLLAMA_HOST = "http://localhost:11434"
MODEL = "gemma2:2b"  # Fast and lightweight (1.6GB)
TIMEOUT = 60  # seconds

def run_llm(prompt, stream=False):
    """
    Sends a prompt to the local Ollama instance and returns the response.
    If stream=True, yields chunks as they arrive.
    """
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
        "options": {
            "num_ctx": 2048,  # Reduced context window for speed
            "temperature": 0.7
        }
    }
    
    try:
        if stream:
            # Streaming mode
            res = requests.post(url, json=payload, stream=True, timeout=TIMEOUT)
            res.raise_for_status()
            for line in res.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                    except json.JSONDecodeError:
                        continue
        else:
            # Non-streaming mode
            res = requests.post(url, json=payload, timeout=TIMEOUT)
            res.raise_for_status()
            return res.json()["message"]["content"]
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The model may be overloaded or the query is too complex."
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure it is running (e.g., 'ollama serve')."
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print(run_llm("Hello, are you ready for hacking?"))

