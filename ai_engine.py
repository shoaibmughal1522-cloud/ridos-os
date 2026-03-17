#!/usr/bin/env python3
"""
RIDOS AI Engine - Offline-first AI with optional online fallback
Tries Anthropic API first, falls back to local rule-based AI if offline.
"""

import os
import json
import subprocess
import socket

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"

def is_online():
    """Check internet connectivity."""
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False

def ask_ai_online(system_prompt, user_message):
    """Call Anthropic API."""
    try:
        import urllib.request
        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except Exception as e:
        return None

def ask_ai(system_prompt, user_message, offline_handler):
    """
    Main AI entry point.
    Online  → Anthropic API
    Offline → local rule-based handler
    """
    if ANTHROPIC_KEY and is_online():
        result = ask_ai_online(system_prompt, user_message)
        if result:
            return result, "online"
    return offline_handler(user_message), "offline"

def run_cmd(cmd):
    """Run shell command, return (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def header(title):
    """Print a styled section header."""
    w = 60
    print("\n" + "═" * w)
    print(f"  {title}")
    print("═" * w)

def status(label, value, ok=True):
    """Print a status line."""
    icon = "✅" if ok else "❌"
    print(f"  {icon}  {label:<30} {value}")
