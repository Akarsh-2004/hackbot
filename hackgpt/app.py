import sys
import os

# Ensure we can import from local package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hackgpt.rag import RAGEngine
from hackgpt.llm import run_llm
from hackgpt.prompt import build_prompt
from hackgpt.parsers import auto_parse
from hackgpt.session import Session
import json

def print_help():
    print("""
Commands:
  /new <session_name>       - Create new session
  /load <session_name>      - Load existing session
  /save                     - Save current session
  /target <ip>              - Set current target
  /status                   - Show current target status
  /ports <port1,port2,...>  - Add discovered ports
  /creds <user:pass>        - Add found credentials
  /note <text>              - Add note to current target
  /help                     - Show this help
  exit/quit                 - Exit application
""")

def main():
    print("\n" + "="*50)
    print("      PERSONAL HACKING ASSISTANT (v1.1)      ")
    print("="*50 + "\n")
    
    # Initialize RAG
    try:
        rag = RAGEngine()
    except Exception as e:
        print(f"[!] Error loading RAG engine: {e}")
        print("[*] Tip: Ensure you have run 'python hackgpt/ingest.py' first.")
        return

    # Initialize session
    session = Session("default")
    print("[*] Session: default")
    print("\n[*] Ready. Type '/help' for commands or 'exit' to quit.\n")
    
    while True:
        try:
            query = input(">> ").strip()
        except KeyboardInterrupt:
            break
            
        if not query:
            continue
        if query.lower() in ["exit", "quit"]:
            break
        
        # Handle commands
        if query.startswith("/"):
            parts = query.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == "/help":
                print_help()
            elif cmd == "/new":
                session = Session(arg or "default")
                print(f"[+] Created new session: {session.session_name}")
            elif cmd == "/load":
                try:
                    session.load(arg)
                    print(f"[+] Loaded session: {session.session_name}")
                except FileNotFoundError as e:
                    print(f"[!] {e}")
            elif cmd == "/save":
                filepath = session.save()
                print(f"[+] Session saved to: {filepath}")
            elif cmd == "/target":
                if arg:
                    session.add_target(arg)
                    print(f"[+] Target set: {arg}")
                else:
                    print("[!] Usage: /target <ip>")
            elif cmd == "/status":
                print(session.get_context_summary())
            elif cmd == "/ports":
                if arg and session.current_target:
                    ports = [p.strip() for p in arg.split(",")]
                    session.add_target(session.current_target, ports=ports)
                    print(f"[+] Added ports: {', '.join(ports)}")
                else:
                    print("[!] Usage: /ports <port1,port2,...> (requires active target)")
            elif cmd == "/creds":
                if arg and session.current_target:
                    session.add_target(session.current_target, credentials=[arg])
                    print(f"[+] Added credentials")
                else:
                    print("[!] Usage: /creds <user:pass> (requires active target)")
            elif cmd == "/note":
                if arg and session.current_target:
                    session.add_target(session.current_target, notes=[arg])
                    print(f"[+] Note added")
                else:
                    print("[!] Usage: /note <text> (requires active target)")
            else:
                print(f"[!] Unknown command: {cmd}. Type /help for available commands.")
            continue
        
        # Check if input is tool output
        parsed_tool = auto_parse(query)
        if parsed_tool:
            print(f"\n[*] Detected {parsed_tool['tool']} output!")
            print(f"[*] Parsed summary: {json.dumps(parsed_tool.get('summary', {}), indent=2)}")
            
            # Auto-update session if target is set
            if session.current_target and parsed_tool['tool'] == 'nmap':
                for host in parsed_tool.get('hosts', []):
                    ports = [p['port'] for p in host.get('ports', []) if p['state'] == 'open']
                    if ports:
                        session.add_target(session.current_target, ports=ports)
                        print(f"[+] Auto-added {len(ports)} ports to session")
            
            query = f"Analyze this {parsed_tool['tool']} output:\n{json.dumps(parsed_tool, indent=2)}"
            
        print("\n[*] Retrieving context...")
        chunks = rag.retrieve(query, k=3)
        
        # Calculate average confidence
        avg_confidence = sum(c.get('similarity_score', 0) for c in chunks) / len(chunks) if chunks else 0
        confidence_level = "HIGH" if avg_confidence > 0.7 else "MEDIUM" if avg_confidence > 0.5 else "LOW"
        
        print(f"[*] Confidence: {confidence_level} ({avg_confidence:.2f})")
        
        # Format context (include session context)
        context_text = ""
        
        # Add session context if available
        if session.current_target:
            context_text += f"**Session Context:**\n{session.get_context_summary()}\n\n"
        
        for i, c in enumerate(chunks):
            source = c.get("file") or c.get("url") or c.get("path") or "unknown"
            score = c.get("similarity_score", 0)
            # Truncate text to reduce prompt size
            text = c['text'][:300] + "..." if len(c['text']) > 300 else c['text']
            context_text += f"-- Source {i+1} ({source}, score: {score:.2f}):\n{text}\n\n"
            
        print("[*] Generating response...")
        prompt = build_prompt(context_text, query, confidence_level)
        
        # Stream response for better UX
        print("\n--- RESPONSE ---\n")
        full_response = ""
        try:
            for chunk in run_llm(prompt, stream=True):
                print(chunk, end="", flush=True)
                full_response += chunk
        except TypeError:
            # Fallback if streaming not supported
            response = run_llm(prompt, stream=False)
            print(response)
            full_response = response
        
        # Log action to session
        if session.current_target:
            session.log_action(query[:100], full_response[:200])
        
        print("\n" + "-"*30 + "\n")

if __name__ == "__main__":
    main()
