#!/usr/bin/env python3
"""
RIDOS AI Network Analyzer - Advanced network diagnostics and analysis
Full offline capability with local network scanning and analysis
"""

import sys
import os
import re
sys.path.insert(0, '/opt/ridos/bin')
from ai_engine import ask_ai, is_online, header, status, run_cmd

SYSTEM_PROMPT = """You are RIDOS AI Network Analyzer. Analyze network diagnostic data and:
1. Identify connectivity issues and their root causes
2. Detect suspicious network activity or open ports
3. Suggest optimizations and security improvements
4. Give exact commands to fix issues
Be technical but clear."""

def get_network_data():
    """Collect comprehensive network information."""
    data = {}

    # Interfaces
    out, _, _ = run_cmd("ip a")
    data["interfaces"] = out

    # Routing
    out, _, _ = run_cmd("ip route")
    data["routing"] = out

    # DNS
    out, _, _ = run_cmd("cat /etc/resolv.conf")
    data["dns"] = out

    # Open ports
    out, _, _ = run_cmd("sudo ss -tuln")
    data["open_ports"] = out

    # Active connections
    out, _, _ = run_cmd("sudo ss -tun | head -30")
    data["connections"] = out

    # WiFi
    out, _, _ = run_cmd("iwconfig 2>/dev/null || echo 'No wireless'")
    data["wifi"] = out

    # ARP table
    out, _, _ = run_cmd("arp -n")
    data["arp"] = out

    # Firewall
    out, _, _ = run_cmd("sudo ufw status 2>/dev/null || sudo iptables -L -n 2>/dev/null | head -20")
    data["firewall"] = out

    # Connectivity tests
    _, _, rc = run_cmd("ping -c2 -W2 8.8.8.8")
    data["internet"] = "Connected" if rc == 0 else "No internet"

    _, _, rc = run_cmd("ping -c2 -W2 192.168.1.1 2>/dev/null || ping -c2 -W2 $(ip route | grep default | awk '{print $3}' | head -1)")
    data["gateway"] = "Reachable" if rc == 0 else "Unreachable"

    # Network errors
    out, _, _ = run_cmd("ip -s link | grep -A4 'errors\\|dropped' | head -20")
    data["errors"] = out

    # Hostname & domain
    out, _, _ = run_cmd("hostname -f 2>/dev/null || hostname")
    data["hostname"] = out

    return data

def offline_analyzer(message):
    """Local network analysis without AI."""
    data = get_network_data()
    issues = []
    suggestions = []

    # Check internet
    if data.get("internet") == "No internet":
        issues.append("🔴 No internet connectivity")
        suggestions.append(
            "Check gateway:\n"
            "  ip route | grep default\n"
            "  ping -c3 $(ip route | grep default | awk '{print $3}')\n"
            "Restart NetworkManager:\n"
            "  sudo systemctl restart NetworkManager"
        )
    else:
        issues.append("🟢 Internet: Connected")

    if data.get("gateway") == "Unreachable":
        issues.append("🔴 Gateway unreachable — check cable/WiFi")
        suggestions.append(
            "Check physical connection, then:\n"
            "  sudo dhclient -v eth0\n"
            "  nmcli connection up $(nmcli -t -f NAME c show --active | head -1)"
        )
    else:
        issues.append("🟢 Gateway: Reachable")

    # Check for suspicious ports
    ports = data.get("open_ports", "")
    suspicious = []
    risky_ports = {"23": "Telnet", "21": "FTP", "3389": "RDP", "5900": "VNC", "1433": "MSSQL", "3306": "MySQL"}
    for port, name in risky_ports.items():
        if f":{port} " in ports or f":{port}\n" in ports:
            suspicious.append(f"{name} (:{port})")

    if suspicious:
        issues.append(f"🟡 Potentially exposed services: {', '.join(suspicious)}")
        suggestions.append(
            "Close unused ports:\n" +
            "\n".join(f"  sudo ufw deny {p}" for p in risky_ports if p in ports)
        )

    # Check DNS
    dns = data.get("dns", "")
    if not dns or "nameserver" not in dns:
        issues.append("🟡 DNS may not be configured")
        suggestions.append(
            "Set Google DNS:\n"
            "  echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf\n"
            "  echo 'nameserver 1.1.1.1' | sudo tee -a /etc/resolv.conf"
        )
    else:
        issues.append("🟢 DNS: Configured")

    # Count active connections
    conn_count = len([l for l in data.get("connections","").split("\n") if "ESTAB" in l])
    issues.append(f"🟢 Active connections: {conn_count}")

    report = [
        "=" * 58,
        "  RIDOS AI Network Analyzer — Offline Report",
        "=" * 58, "",
        "NETWORK STATUS:"
    ]
    report.extend(f"  {i}" for i in issues)

    if suggestions:
        report.append("\nRECOMMENDED ACTIONS:")
        for s in suggestions:
            report.append(s)

    report.extend([
        "\nNETWORK INTERFACES:",
        data.get("interfaces", "N/A"),
        "\nROUTING TABLE:",
        data.get("routing", "N/A"),
        "\nOPEN PORTS:",
        data.get("open_ports", "N/A"),
    ])

    return "\n".join(report)

def run_scan():
    """Run a local network scan."""
    print("\n  Detecting local network range...")
    gw, _, rc = run_cmd("ip route | grep default | awk '{print $3}' | head -1")
    if rc != 0 or not gw:
        print("  Could not detect gateway.")
        return
    # Derive network range from gateway
    parts = gw.split(".")
    if len(parts) == 4:
        network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        print(f"  Scanning {network} (this may take 30s)...")
        out, _, _ = run_cmd(f"sudo nmap -sn {network} --open 2>/dev/null | grep -E 'report|Host'")
        print(out or "  No hosts found or nmap unavailable")

def main():
    os.system("clear")
    header("RIDOS AI Network Analyzer v1.1.0")
    online = is_online()
    print(f"  Mode: {'🌐 Online AI' if online else '📴 Offline (Local Analysis)'}")

    print("\n  Options:")
    print("  1. Full network diagnosis")
    print("  2. Local network scan (nmap)")
    print("  3. Ask a network question")
    print("  4. Exit")

    while True:
        try:
            choice = input("\n  Choice [1-4]: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            print("\n  Collecting network data...")
            data = get_network_data()
            summary = "\n".join(f"{k}: {v[:300]}" for k, v in data.items())
            response, mode = ask_ai(SYSTEM_PROMPT, f"Analyze this network:\n{summary}", offline_analyzer)
            tag = "🌐" if mode == "online" else "📴"
            print(f"\n  {tag} Analysis:\n\n{response}")

        elif choice == "2":
            run_scan()

        elif choice == "3":
            try:
                q = input("\n  Your question: ").strip()
                if q:
                    data = get_network_data()
                    ctx = f"Network context: internet={data['internet']}, gateway={data['gateway']}\nQuestion: {q}"
                    response, mode = ask_ai(SYSTEM_PROMPT, ctx, offline_analyzer)
                    tag = "🌐" if mode == "online" else "📴"
                    print(f"\n  {tag} Answer:\n\n{response}")
            except (KeyboardInterrupt, EOFError):
                pass

        elif choice == "4":
            break

    print("\n  Goodbye!\n")

if __name__ == "__main__":
    main()
