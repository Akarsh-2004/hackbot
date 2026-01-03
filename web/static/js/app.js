// WebSocket connection
const socket = io();

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const statusText = document.getElementById('status-text');
const confidenceFill = document.getElementById('confidence-fill');
const confidenceValue = document.getElementById('confidence-value');
const targetInfo = document.getElementById('target-info');

let currentResponse = null;

// Matrix background animation
const canvas = document.getElementById('matrix-bg');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
const fontSize = 14;
const columns = canvas.width / fontSize;
const drops = Array(Math.floor(columns)).fill(1);

function drawMatrix() {
    ctx.fillStyle = 'rgba(10, 14, 39, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#00f5ff';
    ctx.font = fontSize + 'px monospace';

    for (let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }
        drops[i]++;
    }
}

setInterval(drawMatrix, 50);

// Socket event handlers
socket.on('connect', () => {
    console.log('[+] Socket connected');
    updateStatus('Connecting...');
});

socket.on('connected', (data) => {
    console.log('[+] Connected:', data);
    updateStatus('Connected to HackGPT');
});

socket.on('disconnect', () => {
    console.log('[-] Socket disconnected');
    updateStatus('Disconnected');
});

socket.on('status', (data) => {
    console.log('[*] Status:', data.message);
    updateStatus(data.message);
});

socket.on('confidence', (data) => {
    console.log('[*] Confidence:', data.level, data.score);
    updateConfidence(data.level, data.score);
});

socket.on('tool_detected', (data) => {
    console.log('[*] Tool detected:', data.tool);
    addSystemMessage(`🔧 Detected ${data.tool} output!`);
});

socket.on('response_start', () => {
    console.log('[*] Response started');
    currentResponse = createAssistantMessage();
});

socket.on('response_chunk', (data) => {
    console.log('[*] Chunk received:', data.chunk ? data.chunk.substring(0, 50) : 'empty');
    if (currentResponse && data.chunk) {
        currentResponse.content += data.chunk;
        renderMarkdown(currentResponse.element, currentResponse.content);
        scrollToBottom();
    }
});

socket.on('response_end', (data) => {
    console.log('[+] Response completed in', data.time.toFixed(2), 's');
    updateStatus(`Response generated in ${data.time.toFixed(2)}s`);
    currentResponse = null;
});

socket.on('response', (data) => {
    console.log('[*] Command response:', data);
    if (data.type === 'command') {
        if (data.data.success) {
            addSystemMessage(`✅ ${data.data.message}`);
        } else {
            addSystemMessage(`❌ ${data.data.message}`);
        }
    }
});

socket.on('error', (error) => {
    console.error('[!] Socket error:', error);
    addSystemMessage(`❌ Error: ${error}`);
});

// Send query
function sendQuery() {
    const query = queryInput.value.trim();
    if (!query) return;

    console.log('[>] Sending query:', query.substring(0, 50));
    addUserMessage(query);
    socket.emit('query', { query });

    queryInput.value = '';
    queryInput.style.height = 'auto';
}

// Event listeners
sendBtn.addEventListener('click', sendQuery);
queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
});

// Auto-resize textarea
queryInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});

// UI helper functions
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-content">
            ${escapeHtml(text)}
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function createAssistantMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return {
        element: contentDiv,
        content: ''
    };
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `
        <div class="message-content" style="background: rgba(57, 255, 20, 0.1); border-color: var(--accent-green);">
            ${text}
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function renderMarkdown(element, markdown) {
    try {
        element.innerHTML = marked.parse(markdown);
        element.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    } catch (error) {
        console.error('[!] Markdown rendering error:', error);
        element.textContent = markdown;
    }
}

function updateStatus(message) {
    statusText.textContent = message;
}

function updateConfidence(level, score) {
    const percentage = (score * 100).toFixed(0);
    confidenceFill.style.width = percentage + '%';
    confidenceValue.textContent = level;

    // Color based on level
    if (level === 'HIGH') {
        confidenceFill.style.background = 'var(--accent-green)';
    } else if (level === 'MEDIUM') {
        confidenceFill.style.background = '#ffaa00';
    } else {
        confidenceFill.style.background = '#ff4444';
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Command helpers
function insertCommand(cmd) {
    queryInput.value = cmd;
    queryInput.focus();
}

function sendQuickQuery(query) {
    queryInput.value = query;
    sendQuery();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    queryInput.focus();
    console.log('[*] App initialized');
});
