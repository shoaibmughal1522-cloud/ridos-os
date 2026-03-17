#!/usr/bin/env python3
"""
RIDOS AI Shell - Interactive AI-powered IT assistant
Offline-first: works without internet using local knowledge base
"""

import sys
import os
sys.path.insert(0, '/opt/ridos/bin')
from ai_engine import ask_ai, is_online, header, run_cmd

SYSTEM_PROMPT = """You are RIDOS AI Shell, an expert IT assistant built into RIDOS OS.
You help with system administration, networking, hardware diagnostics, and security.
Give practical, concise terminal commands and explanations.
Always provide offline-friendly solutions when possible."""

OFFLINE_KB = {
    "cpu": "Check CPU: lscpu | grep -E 'Model|Core|Thread|MHz'\nTemperature: sensors\nUsage: htop",
    "memory": "Check RAM: free -h\nDetails: dmidecode -t memory\nTest: memtester 100M 1",
    "disk": "List disks: lsblk\nDisk health: sudo smartctl -a /dev/sda\nUsage: df -h",
    "network": "Interfaces: ip a\nConnections: ss -tuln\nTest: ping -c4 8.8.8.8\nScan: nmap -sn 192.168.1.0/24",
    "wifi": "List WiFi: iwconfig\nNetworks: sudo iwlist scan\nConnect: nmcli dev wifi connect SSID password PASS",
    "security": "Open ports: sudo ss -tuln\nRootkit scan: sudo rkhunter --check\nAudit: sudo lynis audit system",
    "install": "Install package: sudo apt install PACKAGE\nSearch: apt search KEYWORD\nUpdate: sudo apt update && sudo apt upgrade",
    "process": "Running: ps aux | grep PROCESS\nKill: kill -9 PID\nTop processes: htop",
    "firewall": "Status: sudo ufw status\nEnable: sudo ufw enable\nAllow port: sudo ufw allow 22",
    "gpu": "GPU info: lspci | grep -i vga\nIntel status: sudo intel_gpu_top\nDrivers: lsmod | grep drm",
    "usb": "List USB: lsusb\nDetailed: lsusb -v\nUSB events: dmesg | grep usb",
    "boot": "Boot log: journalctl -b\nServices: systemctl list-units --failed\nBoot time: systemd-analyze",
    "log": "System log: journalctl -n 50\nKernel log: dmesg | tail -30\nAuth log: sudo tail /var/log/auth.log",
    "update": "Update system: sudo apt update && sudo apt upgrade\nFull upgrade: sudo apt full-upgrade\nClean: sudo apt autoremove",
    "help": "Available topics: cpu, memory, disk, network, wifi, security, install, process, firewall, gpu, usb, boot, log, update",
}

def offline_handler(message):
    msg = message.lower()
    for key, val in OFFLINE_KB.items():
        if key in msg:
            return f"[Offline Mode] Commands for {key}:\n\n{val}"
    # Try to give smart generic help
    if any(w in msg for w in ["how", "what", "why", "show", "check"]):
        return (
            "[Offline Mode] I don't have a specific answer for that offline.\n"
            "Try: 'help' to see available topics, or connect to internet for full AI.\n\n"
            "Quick system check:\n"
            "  lshw -short          - all hardware\n"
            "  journalctl -b -p err - boot errors\n"
            "  systemctl --failed   - failed services"
        )
    return (
        "[Offline Mode] Type a topic like: cpu, memory, disk, network, security, boot\n"
        "Or connect to internet for full AI assistance."
    )

def collect_system_context():
    """Gather quick system info to include in AI context."""
    ctx = []
    out, _, _ = run_cmd("uname -r")
    if out: ctx.append(f"Kernel: {out}")
    out, _, _ = run_cmd("free -h | awk 'NR==2{print $2\" total, \"$3\" used\"}'")
    if out: ctx.append(f"RAM: {out}")
    out, _, _ = run_cmd("df -h / | awk 'NR==2{print $2\" total, \"$5\" used\"}'")
    if out: ctx.append(f"Disk: {out}")
    out, _, _ = run_cmd("systemctl --failed --no-legend | wc -l")
    if out and out != "0": ctx.append(f"Failed services: {out}")
    return " | ".join(ctx)

def main():
    os.system("clear")
    header("RIDOS AI Shell v1.1.0 Baghdad")
    online = is_online()
    mode = "🌐 Online (Anthropic AI)" if online else "📴 Offline (Local AI)"
    print(f"  Mode: {mode}")
    print(f"  System: {collect_system_context()}")
    print(f"\n  Type your question, or: 'help', 'sysinfo', 'exit'")
    print("═" * 60)

    while True:
        try:
            user_input = input("\n  RIDOS> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Goodbye!\n")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("\n  Goodbye!\n")
            break
        if user_input.lower() == "sysinfo":
            print(f"\n  {collect_system_context()}")
            continue
        if user_input.lower() == "clear":
            os.system("clear")
            continue

        print("\n  Thinking...", end="\r")
        sys_ctx = collect_system_context()
        full_prompt = f"System context: {sys_ctx}\n\nUser question: {user_input}"
        response, mode_used = ask_ai(SYSTEM_PROMPT, full_prompt, offline_handler)
        tag = "🌐" if mode_used == "online" else "📴"
        print(f"  {tag} ", end="")
        print(f"\n{response}\n")

if __name__ == "__main__":
    main()
