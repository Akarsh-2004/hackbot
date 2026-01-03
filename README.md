# 🔐 HackGPT - Personal Penetration Testing Assistant

A powerful, offline AI-powered penetration testing assistant with RAG (Retrieval-Augmented Generation) capabilities. Built for security researchers and ethical hackers.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ Features

- 🧠 **RAG-Powered Knowledge Base** - 3,837+ curated chunks from security books and walkthroughs
- ⚡ **Fast Responses** - Optimized for 2-4 second response times
- 🔧 **Tool Output Parsing** - Auto-detects and parses nmap, nikto, and other tool outputs
- 💾 **Session Management** - Track targets, ports, credentials, and attack timelines
- 📊 **Confidence Scoring** - HIGH/MEDIUM/LOW confidence indicators
- 🌐 **Modern Web UI** - Sleek black & white hacking-themed interface
- 💻 **CLI Interface** - Terminal-based option for command-line users
- 🔒 **100% Offline** - All data stays on your machine

## 🎯 Use Cases

- Security research and vulnerability analysis
- Penetration testing workflow assistance
- Learning offensive security techniques
- Quick payload and exploit reference
- CTF (Capture The Flag) competitions
- Red team operations planning

## 📸 Screenshots

### Web Interface
```
┌─────────────────────────────────────────────────┐
│  HACKGPT                    Confidence: HIGH    │
├─────────────────────────────────────────────────┤
│  Target Info    │  Chat Interface               │
│  10.10.10.1     │  > gimme xss payloads         │
│  Ports: 22,80   │                               │
│  Creds: 2       │  <script>alert(1)</script>    │
│                 │  <img src=x onerror=alert(1)> │
│  Commands       │  ...                          │
│  /target        │                               │
│  /ports         │                               │
│  /status        │                               │
└─────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) installed
- 4GB+ RAM
- 10GB+ disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Akarsh-2004/hackgpt.git
   cd hackgpt
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r web/requirements.txt
   ```

3. **Install and start Ollama**
   ```bash
   # Install Ollama from https://ollama.com/
   
   # Pull the model
   ollama pull gemma2:2b
   
   # Start Ollama (if not auto-started)
   ollama serve
   ```

4. **Knowledge Base (Optional)**
   
   The repository already includes a pre-computed vector index and data chunks (`data/index.faiss` and `data/chunks.jsonl`). You can **skip this step** and start the app immediately.
   
   If you want to add your own books or update the index, run:
   ```bash
   python hackgpt/ingest.py
   ```
   
   This will:
   - Process PDF books from `Books/` directory
   - Clone security repositories (PayloadsAllTheThings)
   - Update the FAISS vector index (~5-10 minutes)

5. **Run the application**

   **Web UI** (Recommended):
   ```bash
   python web/app.py
   ```
   Open browser: `http://localhost:5000`

   **CLI**:
   ```bash
   python hackgpt/app.py
   ```

## 📚 Project Structure

```
hackgpt/
├── hackgpt/              # Core modules
│   ├── app.py           # CLI application
│   ├── rag.py           # RAG engine (FAISS + embeddings)
│   ├── llm.py           # Ollama LLM integration
│   ├── prompt.py        # Prompt templates
│   ├── parsers.py       # Tool output parsers (nmap, nikto)
│   ├── session.py       # Session/target management
│   ├── evaluator.py     # Metrics and evaluation
│   └── ingest.py        # Data ingestion pipeline
├── web/                  # Web UI
│   ├── app.py           # Flask backend with WebSocket
│   ├── static/
│   │   ├── index.html   # Main UI
│   │   ├── css/style.css # Black & white theme
│   │   └── js/app.js    # WebSocket client
│   └── requirements.txt
├── data/
│   ├── index.faiss      # Vector index
│   ├── chunks.jsonl     # Knowledge chunks
│   ├── sessions/        # Saved sessions
│   └── walkthroughs/    # GitHub repos
├── Books/               # PDF security books (add your own)
├── tests/               # Regression tests
│   ├── test_queries.json
│   └── run_tests.py
└── requirements.txt
```

## 💡 Usage Examples

### Web UI

1. **Basic Query**
   ```
   >> what is sql injection
   ```

2. **Get Payloads**
   ```
   >> gimme 10 xss payloads
   ```

3. **Session Management**
   ```
   >> /target 10.10.10.1
   >> /ports 22,80,443
   >> /status
   >> /save
   ```

4. **Tool Output Analysis**
   Paste nmap output directly:
   ```
   Nmap scan report for 10.10.10.1
   PORT     STATE SERVICE
   22/tcp   open  ssh
   80/tcp   open  http
   445/tcp  open  microsoft-ds
   ```
   
   HackGPT will auto-detect, parse, and analyze it!

### CLI

```bash
>> How do I enumerate SMB on port 445?
>> What are common Linux privilege escalation techniques?
>> /target 192.168.1.100
>> /ports 22,80,443,3389
```

## 🔧 Configuration

### Change LLM Model

Edit `hackgpt/llm.py`:
```python
MODEL = "gemma2:2b"  # Options: gemma2:1b, mistral, llama2
```

### Adjust Performance

Edit `web/app.py`:
```python
chunks = rag.retrieve(query, k=2)  # Reduce for speed (default: 2)
text = c['text'][:150]  # Reduce context size (default: 150)
```

### Add Custom Knowledge

1. Add PDF books to `Books/` directory
2. Add URLs to `hackgpt/scraper.py`
3. Re-run ingestion:
   ```bash
   python hackgpt/ingest.py
   ```

## 🧪 Testing

Run regression tests:
```bash
python tests/run_tests.py
```

Expected output:
```
==================================================
Running Regression Tests
==================================================

[TEST] smb_enum
  Confidence: HIGH
  Keyword Coverage: 100.0%
  Response Time: 3.21s
  Status: ✅ PASS

Passed: 5/5 (100.0%)
Avg Response Time: 3.45s
```

## 🌐 Deployment

### Quick Tunnel (ngrok)
```bash
# Terminal 1
python web/app.py

# Terminal 2
ngrok http 5000
```

### VPS Deployment
See [deployment_guide.md](deployment_guide.md) for detailed instructions.

## 📊 Performance

| Metric | Value |
|--------|-------|
| Knowledge Chunks | 3,837 |
| Avg Response Time | 2-4s |
| Model Size | 1.6GB (gemma2:2b) |
| Memory Usage | ~2GB RAM |
| Disk Space | ~8GB |

## 🔒 Security Considerations

⚠️ **IMPORTANT**: This tool is designed for **authorized security research only**.

- Add authentication before deploying publicly
- Use HTTPS/SSL for remote access
- Implement rate limiting
- Whitelist IPs for production
- Never expose on public internet without protection

### Add Basic Auth

```python
# Install
pip install Flask-HTTPAuth

# Add to web/app.py
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

users = {"admin": "your-password"}

@auth.verify_password
def verify(username, password):
    return users.get(username) == password

@app.route('/')
@auth.login_required
def index():
    return app.send_static_file('index.html')
```

## 🛠️ Troubleshooting

### Ollama Connection Error
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Slow Responses
- Use smaller model: `ollama pull gemma2:1b`
- Reduce chunks: `k=1` in `web/app.py`
- Reduce context size: `text[:100]`

### Import Errors
```bash
pip install -r requirements.txt --upgrade
pip install -r web/requirements.txt --upgrade
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## ⚠️ Disclaimer

This tool is for **educational and authorized security research purposes only**. Users are responsible for complying with all applicable laws and regulations. The authors assume no liability for misuse.

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) - Local LLM runtime
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) - Security payloads
- [sentence-transformers](https://www.sbert.net/) - Embedding models

## 📧 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Issues: [GitHub Issues](https://github.com/yourusername/hackgpt/issues)

---

**⭐ Star this repo if you find it useful!**

**🔐 Happy Hacking (Ethically)!**
