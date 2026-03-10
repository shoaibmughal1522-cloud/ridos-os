"""
╔══════════════════════════════════════════════════════════════╗
║  RIDOS OS v1.1 — Web GUI                                    ║
║  Copyright (C) 2026 RIDOS OS Project — GPL v3               ║
║  https://github.com/alexeaiskinder-mea/ridos-os             ║
╚══════════════════════════════════════════════════════════════╝

Browser-based AI dashboard accessible on port 8080.
Access from any device on the same network.

Start: python3 /opt/ridos/bin/web_gui.py
Open:  http://localhost:8080  or  http://<RIDOS-IP>:8080

WARNING: No authentication — use on trusted networks only.
"""

import asyncio
import json
import os
import socket
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit

VERSION  = "1.1.0"
CODENAME = "Basra"
PORT     = 8080
SOCKET_PATH = "/run/ridos.sock"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ── HTML template (single file, no external deps) ────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RIDOS OS — Web Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.0/socket.io.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  :root {
    --bg:#0a0612;--bg2:#110828;--bg3:#1a0f35;
    --border:#3b1a6b;--text:#e9d5ff;--muted:#9333ea;
    --purple:#7c3aed;--lt:#a855f7;--acc:#c084fc;
    --green:#4ade80;--red:#f87171;--amber:#fbbf24;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Space Grotesk',sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column}

  /* Header */
  header{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 24px;height:52px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
  .logo{display:flex;align-items:center;gap:10px}
  .hex{width:32px;height:32px;background:linear-gradient(135deg,var(--purple),var(--lt));clip-path:polygon(50% 0%,93% 25%,93% 75%,50% 100%,7% 75%,7% 25%);display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;color:#fff}
  .logo-text{font-weight:700;font-size:15px;color:var(--acc)}
  .logo-sub{font-size:11px;color:var(--muted);margin-top:1px}
  .status-dot{width:8px;height:8px;border-radius:50%;background:var(--green)}
  .status-dot.offline{background:var(--red)}
  .hdr-right{display:flex;align-items:center;gap:16px;font-size:12px;color:var(--muted)}
  #clock{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--lt)}

  /* Layout */
  .layout{flex:1;display:flex;overflow:hidden}

  /* Sidebar */
  .sidebar{width:220px;background:var(--bg2);border-left:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0}
  .sb-hdr{padding:14px 16px 8px;font-size:10px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase}
  .stat-card{margin:4px 10px;background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:10px 12px}
  .stat-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px}
  .stat-val{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text)}
  .bar{height:3px;background:var(--bg);border-radius:2px;margin-top:5px;overflow:hidden}
  .bar-fill{height:100%;background:var(--purple);border-radius:2px;transition:width 0.5s}
  .sb-divider{height:1px;background:var(--border);margin:10px 10px}
  .quick-btn{display:block;margin:3px 10px;padding:8px 12px;background:var(--bg3);border:1px solid var(--border);border-radius:5px;color:var(--muted);font-size:12px;cursor:pointer;transition:all 0.15s;text-align:left;font-family:'Space Grotesk',sans-serif;width:calc(100% - 20px)}
  .quick-btn:hover{border-color:var(--purple);color:var(--lt);background:rgba(124,58,237,0.1)}

  /* Chat area */
  .chat-area{flex:1;display:flex;flex-direction:column;overflow:hidden}
  .messages{flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:12px}
  .msg{display:flex;gap:12px;max-width:82%;animation:fadeUp 0.2s ease}
  .msg.user{align-self:flex-end;flex-direction:row-reverse}
  @keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
  .avatar{width:32px;height:32px;border-radius:8px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;font-family:'JetBrains Mono',monospace}
  .avatar.ai{background:rgba(124,58,237,0.2);border:1px solid var(--purple);color:var(--lt)}
  .avatar.user{background:rgba(168,85,247,0.15);border:1px solid var(--border);color:var(--acc)}
  .bubble{padding:12px 16px;border-radius:10px;font-size:13.5px;line-height:1.7;max-width:100%}
  .msg.ai .bubble{background:var(--bg2);border:1px solid var(--border);border-radius:2px 10px 10px 10px}
  .msg.user .bubble{background:rgba(124,58,237,0.15);border:1px solid var(--purple);border-radius:10px 2px 10px 10px}
  .msg-meta{font-size:10px;color:var(--muted);margin-top:4px;font-family:'JetBrains Mono',monospace}
  .bubble pre{background:#05030f;border:1px solid var(--border);padding:10px 14px;border-radius:5px;font-family:'JetBrains Mono',monospace;font-size:11.5px;overflow-x:auto;margin-top:8px;line-height:1.7;color:#d8b4fe}
  .typing{display:flex;gap:4px;padding:10px 14px}
  .typing span{width:6px;height:6px;background:var(--purple);border-radius:50%;animation:bounce 1s infinite}
  .typing span:nth-child(2){animation-delay:0.15s}
  .typing span:nth-child(3){animation-delay:0.3s}
  @keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}

  /* Input */
  .input-area{padding:16px 24px;background:var(--bg2);border-top:1px solid var(--border);display:flex;gap:10px;align-items:flex-end}
  textarea{flex:1;background:var(--bg3);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:10px 14px;font-family:'Space Grotesk',sans-serif;font-size:13.5px;resize:none;min-height:44px;max-height:140px;line-height:1.5;outline:none;transition:border-color 0.15s}
  textarea:focus{border-color:var(--purple)}
  textarea::placeholder{color:var(--muted)}
  #send-btn{background:var(--purple);border:none;color:#fff;width:44px;height:44px;border-radius:8px;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;transition:all 0.15s;flex-shrink:0}
  #send-btn:hover{background:var(--lt)}
  #send-btn:disabled{background:var(--bg3);color:var(--muted);cursor:not-allowed}

  /* Welcome screen */
  .welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;text-align:center;padding:40px}
  .welcome .big-hex{width:80px;height:80px;background:linear-gradient(135deg,var(--purple),var(--lt));clip-path:polygon(50% 0%,93% 25%,93% 75%,50% 100%,7% 75%,7% 25%);display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:32px;color:#fff;margin-bottom:20px}
  .welcome h2{font-size:22px;color:var(--acc);margin-bottom:8px}
  .welcome p{font-size:13px;color:var(--muted);max-width:400px;line-height:1.7}
  .suggestion-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:24px;max-width:480px}
  .suggestion{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;cursor:pointer;font-size:12px;color:var(--muted);transition:all 0.15s;text-align:left}
  .suggestion:hover{border-color:var(--purple);color:var(--lt)}
  .suggestion strong{display:block;color:var(--text);font-size:11px;margin-bottom:2px}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="hex">R</div>
    <div>
      <div class="logo-text">RIDOS OS</div>
      <div class="logo-sub">Web Dashboard — v{{ version }}</div>
    </div>
  </div>
  <div class="hdr-right">
    <div style="display:flex;align-items:center;gap:6px">
      <div class="status-dot" id="conn-dot"></div>
      <span id="conn-label">Connected</span>
    </div>
    <span>|</span>
    <span id="clock"></span>
  </div>
</header>

<div class="layout">

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sb-hdr">System</div>
    <div class="stat-card">
      <div class="stat-label">CPU</div>
      <div class="stat-val" id="cpu-val">–</div>
      <div class="bar"><div class="bar-fill" id="cpu-bar" style="width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">RAM</div>
      <div class="stat-val" id="ram-val">–</div>
      <div class="bar"><div class="bar-fill" id="ram-bar" style="width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Network</div>
      <div class="stat-val" id="net-val">–</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">IP Address</div>
      <div class="stat-val" id="ip-val">–</div>
    </div>

    <div class="sb-divider"></div>
    <div class="sb-hdr">Quick Actions</div>
    <button class="quick-btn" onclick="quickAsk('scan my local network')">🔍 Scan Network</button>
    <button class="quick-btn" onclick="quickAsk('show open ports')">🔒 Open Ports</button>
    <button class="quick-btn" onclick="quickAsk('show system status')">📊 System Status</button>
    <button class="quick-btn" onclick="quickAsk('show top processes')">⚙ Processes</button>
    <button class="quick-btn" onclick="quickAsk('what is my ip address')">🌐 My IP</button>
    <button class="quick-btn" onclick="quickAsk('check disk space')">💾 Disk Space</button>
  </aside>

  <!-- Chat -->
  <div class="chat-area">
    <div class="messages" id="messages">
      <div class="welcome" id="welcome">
        <div class="big-hex">R</div>
        <h2>RIDOS AI Assistant</h2>
        <p>Ask me anything about your system, network, or IT tasks. I can run commands, search for CVEs, and explain technical concepts.</p>
        <div class="suggestion-grid">
          <div class="suggestion" onclick="quickAsk('scan my local network')">
            <strong>🔍 Network Scan</strong>Discover devices on your LAN
          </div>
          <div class="suggestion" onclick="quickAsk('CVE-2024-6387')">
            <strong>🛡 CVE Lookup</strong>Look up a vulnerability
          </div>
          <div class="suggestion" onclick="quickAsk('what ports are open on this machine')">
            <strong>🔒 Port Check</strong>See what's listening
          </div>
          <div class="suggestion" onclick="quickAsk('show system status')">
            <strong>📊 System Info</strong>CPU, RAM, disk, network
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <textarea id="input" placeholder="Ask RIDOS anything — network scan, CVE lookup, system status..." rows="1"></textarea>
      <button id="send-btn" onclick="send()">➤</button>
    </div>
  </div>

</div>

<script>
  const socket = io();
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('input');
  const welcome = document.getElementById('welcome');
  let isWaiting = false;

  // Clock
  function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent =
      now.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  }
  setInterval(updateClock, 1000);
  updateClock();

  // System stats
  function updateStats() {
    fetch('/api/stats').then(r => r.json()).then(d => {
      document.getElementById('cpu-val').textContent = d.cpu + '%';
      document.getElementById('cpu-bar').style.width = d.cpu + '%';
      document.getElementById('ram-val').textContent = d.ram_used + ' / ' + d.ram_total + ' MB';
      document.getElementById('ram-bar').style.width = d.ram_pct + '%';
      document.getElementById('net-val').textContent = d.online ? '🟢 Online' : '🔴 Offline';
      document.getElementById('ip-val').textContent = d.ip;
    }).catch(() => {});
  }
  updateStats();
  setInterval(updateStats, 5000);

  // Connection status
  socket.on('connect',    () => {
    document.getElementById('conn-dot').className = 'status-dot';
    document.getElementById('conn-label').textContent = 'Connected';
  });
  socket.on('disconnect', () => {
    document.getElementById('conn-dot').className = 'status-dot offline';
    document.getElementById('conn-label').textContent = 'Disconnected';
  });

  function ts() {
    return new Date().toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit'});
  }

  function addMsg(role, text, model) {
    if (welcome) welcome.style.display = 'none';
    const msg = document.createElement('div');
    msg.className = 'msg ' + role;
    const av = role === 'ai' ? 'R' : 'U';
    const badge = model ? `<span style="font-size:10px;color:var(--muted);margin-left:6px">[${model}]</span>` : '';
    // Format code blocks
    let formatted = text
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/`([^`]+)`/g,'<code style="background:var(--bg3);padding:1px 5px;border-radius:3px;font-family:JetBrains Mono,monospace;font-size:11.5px;color:var(--acc)">$1</code>');
    // Multi-line code blocks
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre>$1</pre>');
    msg.innerHTML = `
      <div class="avatar ${role}">${av}</div>
      <div>
        <div class="bubble">${formatted}</div>
        <div class="msg-meta">${ts()}${badge}</div>
      </div>`;
    messagesEl.appendChild(msg);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addTyping() {
    const t = document.createElement('div');
    t.className = 'msg ai'; t.id = 'typing-indicator';
    t.innerHTML = `<div class="avatar ai">R</div><div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
    messagesEl.appendChild(t);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function removeTyping() {
    const t = document.getElementById('typing-indicator');
    if (t) t.remove();
  }

  function send() {
    const text = inputEl.value.trim();
    if (!text || isWaiting) return;
    addMsg('user', text, null);
    inputEl.value = ''; inputEl.style.height = '44px';
    isWaiting = true;
    document.getElementById('send-btn').disabled = true;
    addTyping();
    socket.emit('message', {text});
  }

  socket.on('response', (data) => {
    removeTyping();
    addMsg('ai', data.response, data.model);
    isWaiting = false;
    document.getElementById('send-btn').disabled = false;
  });

  socket.on('error', (data) => {
    removeTyping();
    addMsg('ai', '⚠ ' + data.message, 'error');
    isWaiting = false;
    document.getElementById('send-btn').disabled = false;
  });

  function quickAsk(text) {
    inputEl.value = text;
    send();
  }

  // Enter to send, Shift+Enter for newline
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  // Auto-resize textarea
  inputEl.addEventListener('input', () => {
    inputEl.style.height = '44px';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
  });
</script>
</body>
</html>"""

# ── System stats API ──────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML, version=VERSION)

@app.route("/api/stats")
def stats():
    data = {"cpu": 0, "ram_used": 0, "ram_total": 0, "ram_pct": 0,
            "online": False, "ip": "unknown"}
    try:
        import psutil
        data["cpu"] = round(psutil.cpu_percent(interval=0.3), 1)
        m = psutil.virtual_memory()
        data["ram_used"]  = m.used  // 1024 // 1024
        data["ram_total"] = m.total // 1024 // 1024
        data["ram_pct"]   = round(m.percent, 1)
    except ImportError:
        pass
    try:
        data["ip"] = socket.gethostbyname(socket.gethostname())
    except Exception:
        pass
    try:
        r = subprocess.run(["ping", "-c1", "-W2", "8.8.8.8"],
                           capture_output=True, timeout=3)
        data["online"] = r.returncode == 0
    except Exception:
        pass
    return jsonify(data)

# ── Socket.IO message handler ─────────────────────────────────
conversation = []

@socketio.on("message")
def handle_message(data):
    global conversation
    prompt = data.get("text", "").strip()
    if not prompt:
        emit("error", {"message": "Empty message"})
        return

    # Try daemon socket first
    try:
        loop = asyncio.new_event_loop()
        response, model = loop.run_until_complete(ask_daemon(prompt))
        loop.close()
    except Exception as e:
        response = f"Error connecting to RIDOS daemon: {e}\nMake sure ridos-daemon is running: sudo systemctl start ridos-daemon"
        model = "error"

    conversation.append({"role": "user",      "content": prompt})
    conversation.append({"role": "assistant",  "content": response})
    if len(conversation) > 20:
        conversation = conversation[-20:]

    emit("response", {"response": response, "model": model})

async def ask_daemon(prompt: str) -> tuple:
    if not os.path.exists(SOCKET_PATH):
        raise ConnectionError("RIDOS daemon socket not found")
    reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)
    payload = json.dumps({"prompt": prompt, "context": conversation[-10:]})
    writer.write(payload.encode())
    writer.write_eof()
    await writer.drain()
    data = await asyncio.wait_for(reader.read(65536), timeout=45)
    writer.close()
    r = json.loads(data.decode())
    return r["response"], r.get("model", "unknown")

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    host_ip = "0.0.0.0"
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "localhost"

    print(f"""
╔══════════════════════════════════════════════════════╗
║  RIDOS OS v{VERSION} — Web GUI                        ║
║  Copyright (C) 2026 RIDOS OS Project — GPL v3        ║
╠══════════════════════════════════════════════════════╣
║  Local:   http://localhost:{PORT}                     ║
║  Network: http://{local_ip:<20}:{PORT}             ║
╚══════════════════════════════════════════════════════╝
""")
    socketio.run(app, host=host_ip, port=PORT, debug=False)
