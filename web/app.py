import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import time

from hackgpt.rag import RAGEngine
from hackgpt.llm import run_llm
from hackgpt.prompt import build_prompt
from hackgpt.parsers import auto_parse
from hackgpt.session import Session

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = 'hackgpt-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize RAG engine
rag = RAGEngine()
sessions = {}  # {sid: Session}
conversation_history = {}  # {sid: [messages]} - Cache last 10 messages

@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    sessions[sid] = Session("default")
    conversation_history[sid] = []
    emit('connected', {'message': 'Connected to HackGPT', 'session': 'default'})
    print(f"[+] Client connected: {sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in sessions:
        del sessions[sid]
    if sid in conversation_history:
        del conversation_history[sid]
    print(f"[-] Client disconnected: {sid}")

@socketio.on('query')
def handle_query(data):
    sid = request.sid
    query = data.get('query', '')
    session = sessions.get(sid, Session("default"))
    
    print(f"[*] Query from {sid}: {query[:50]}...")
    
    start_time = time.time()
    
    # Check for commands
    if query.startswith('/'):
        result = handle_command(query, session)
        emit('response', {'type': 'command', 'data': result})
        return
    
    # Add to conversation history
    if sid not in conversation_history:
        conversation_history[sid] = []
    conversation_history[sid].append({'role': 'user', 'content': query})
    
    # Keep only last 10 messages
    if len(conversation_history[sid]) > 10:
        conversation_history[sid] = conversation_history[sid][-10:]
    
    # Parse tool output
    parsed_tool = auto_parse(query)
    if parsed_tool:
        emit('tool_detected', {'tool': parsed_tool['tool'], 'summary': parsed_tool.get('summary', {})})
        
        # Auto-update session
        if session.current_target and parsed_tool['tool'] == 'nmap':
            for host in parsed_tool.get('hosts', []):
                ports = [p['port'] for p in host.get('ports', []) if p['state'] == 'open']
                if ports:
                    session.add_target(session.current_target, ports=ports)
        
        query = f"Analyze this {parsed_tool['tool']} output:\n{json.dumps(parsed_tool, indent=2)}"
    
    # Retrieve context
    emit('status', {'message': 'Retrieving context...'})
    chunks = rag.retrieve(query, k=2)  # Reduced from 3 to 2
    
    # Calculate confidence
    avg_confidence = sum(c.get('similarity_score', 0) for c in chunks) / len(chunks) if chunks else 0
    confidence_level = "HIGH" if avg_confidence > 0.7 else "MEDIUM" if avg_confidence > 0.5 else "LOW"
    
    emit('confidence', {'level': confidence_level, 'score': avg_confidence})
    
    # Format context with conversation history
    context_text = ""
    
    # Add conversation history for context
    if len(conversation_history[sid]) > 1:
        context_text += "**Recent Conversation:**\n"
        for msg in conversation_history[sid][-5:]:  # Last 5 messages
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_text += f"{role}: {msg['content'][:100]}...\n"
        context_text += "\n"
    
    if session.current_target:
        context_text += f"**Session Context:**\n{session.get_context_summary()}\n\n"
    
    sources = []
    for i, c in enumerate(chunks):
        source = c.get("file") or c.get("url") or c.get("path") or "unknown"
        score = c.get("similarity_score", 0)
        text = c['text'][:150] + "..." if len(c['text']) > 150 else c['text']  # Reduced from 300 to 150
        context_text += f"-- Source {i+1} ({source}, score: {score:.2f}):\n{text}\n\n"
        sources.append({'source': source, 'score': score})
    
    emit('sources', {'sources': sources})
    
    # Generate response
    emit('status', {'message': 'Generating response...'})
    prompt = build_prompt(context_text, query, confidence_level)
    
    print(f"[*] Generating response for {sid}...")
    
    # Stream response
    emit('response_start', {})
    full_response = ""
    
    try:
        for chunk in run_llm(prompt, stream=True):
            if chunk:  # Only emit non-empty chunks
                emit('response_chunk', {'chunk': chunk})
                full_response += chunk
                socketio.sleep(0.001)  # Reduced from 0.01 to 0.001 for smoother streaming
    except (TypeError, StopIteration) as e:
        print(f"[!] Streaming failed, falling back to non-streaming: {e}")
        response = run_llm(prompt, stream=False)
        emit('response_chunk', {'chunk': response})
        full_response = response
    
    # Add assistant response to history
    conversation_history[sid].append({'role': 'assistant', 'content': full_response})
    
    response_time = time.time() - start_time
    emit('response_end', {'time': response_time})
    
    print(f"[+] Response completed in {response_time:.2f}s")
    
    # Log to session
    if session.current_target:
        session.log_action(query[:100], full_response[:200])

def handle_command(cmd, session):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None
    
    if command == '/target':
        if arg:
            session.add_target(arg)
            return {'success': True, 'message': f'Target set: {arg}'}
        return {'success': False, 'message': 'Usage: /target <ip>'}
    
    elif command == '/status':
        return {'success': True, 'message': session.get_context_summary()}
    
    elif command == '/ports':
        if arg and session.current_target:
            ports = [p.strip() for p in arg.split(",")]
            session.add_target(session.current_target, ports=ports)
            return {'success': True, 'message': f'Added ports: {", ".join(ports)}'}
        return {'success': False, 'message': 'Usage: /ports <port1,port2,...>'}
    
    elif command == '/creds':
        if arg and session.current_target:
            session.add_target(session.current_target, credentials=[arg])
            return {'success': True, 'message': 'Credentials added'}
        return {'success': False, 'message': 'Usage: /creds <user:pass>'}
    
    elif command == '/save':
        filepath = session.save()
        return {'success': True, 'message': f'Session saved to: {filepath}'}
    
    elif command == '/new':
        session.__init__(arg or "default")
        return {'success': True, 'message': f'New session: {session.session_name}'}
    
    return {'success': False, 'message': f'Unknown command: {command}'}

if __name__ == '__main__':
    print("\n" + "="*50)
    print("      HACKGPT WEB SERVER      ")
    print("="*50)
    print("\n[*] Starting server on http://localhost:5000")
    print("[*] Press Ctrl+C to stop\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
