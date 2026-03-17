#!/usr/bin/env python3
"""
RIDOS AI Security Scanner - Comprehensive security audit and threat detection
Full offline capability using lynis, rkhunter, chkrootkit, ufw
"""

import sys
import os
import re
sys.path.insert(0, '/opt/ridos/bin')
from ai_engine import ask_ai, is_online, header, status, run_cmd

SYSTEM_PROMPT = """You are RIDOS AI Security Scanner. Analyze security audit data and:
1. Identify vulnerabilities and risks clearly
2. Rate each: CRITICAL / HIGH / MEDIUM / LOW
3. Give exact hardening commands for each issue
4. Prioritize by impact
Be thorough but actionable. Focus on practical fixes."""

def collect_security_data():
    """Collect comprehensive security audit data."""
    data = {}

    # Users and sudo
    out, _, _ = run_cmd("cat /etc/passwd | grep -v nologin | grep -v false | grep bash")
    data["shell_users"] = out
    out, _, _ = run_cmd("sudo cat /etc/sudoers 2>/dev/null | grep -v '#' | grep -v '^$'")
    data["sudoers"] = out
    out, _, _ = run_cmd("lastlog 2>/dev/null | grep -v 'Never' | head -10")
    data["last_logins"] = out

    # SSH config
    out, _, _ = run_cmd("sudo cat /etc/ssh/sshd_config 2>/dev/null | grep -v '#' | grep -v '^$'")
    data["ssh_config"] = out

    # Open ports and services
    out, _, _ = run_cmd("sudo ss -tuln")
    data["open_ports"] = out
    out, _, _ = run_cmd("sudo ss -tun | grep ESTAB")
    data["connections"] = out

    # Firewall
    out, _, _ = run_cmd("sudo ufw status verbose 2>/dev/null")
    data["ufw"] = out
    out, _, _ = run_cmd("sudo iptables -L -n 2>/dev/null | head -30")
    data["iptables"] = out

    # SUID/SGID files (potential privilege escalation)
    out, _, _ = run_cmd("find / -perm /6000 -type f 2>/dev/null | grep -v proc | head -20")
    data["suid_files"] = out

    # World-writable files
    out, _, _ = run_cmd("find /etc -writable -type f 2>/dev/null | head -10")
    data["writable_etc"] = out

    # Failed login attempts
    out, _, _ = run_cmd("sudo journalctl _SYSTEMD_UNIT=sshd.service 2>/dev/null | grep Failed | tail -10")
    data["failed_logins"] = out or "None"

    # Running services
    out, _, _ = run_cmd("systemctl list-units --type=service --state=running --no-legend | head -20")
    data["running_services"] = out

    # Installed security tools
    tools = {}
    for tool in ["ufw", "fail2ban", "rkhunter", "chkrootkit", "lynis", "clamav"]:
        _, _, rc = run_cmd(f"which {tool} 2>/dev/null")
        tools[tool] = "installed" if rc == 0 else "not installed"
    data["security_tools"] = str(tools)

    # Check for rootkits (quick)
    out, _, _ = run_cmd("sudo rkhunter --check --sk --nocolors 2>/dev/null | grep -E 'Warning|Found' | head -15")
    data["rkhunter"] = out or "Clean or not available"

    # Password policy
    out, _, _ = run_cmd("sudo cat /etc/login.defs | grep -E 'PASS_MAX|PASS_MIN|PASS_WARN' | grep -v '#'")
    data["password_policy"] = out

    # World readable sensitive files
    out, _, _ = run_cmd("ls -la /etc/shadow /etc/gshadow 2>/dev/null")
    data["shadow_perms"] = out

    return data

def offline_security_scanner(message):
    """Local security analysis without AI API."""
    data = collect_security_data()
    findings = []  # (severity, title, detail, fix)

    # Check firewall
    ufw = data.get("ufw", "")
    if "inactive" in ufw.lower() or not ufw:
        findings.append(("HIGH", "Firewall disabled",
            "UFW firewall is inactive — system is exposed",
            "sudo ufw default deny incoming\nsudo ufw default allow outgoing\nsudo ufw allow ssh\nsudo ufw enable"))
    else:
        findings.append(("OK", "Firewall active", ufw[:100], ""))

    # Check SSH
    ssh = data.get("ssh_config", "")
    if "PermitRootLogin yes" in ssh:
        findings.append(("CRITICAL", "SSH root login enabled",
            "Root can log in via SSH — major security risk",
            "sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config\nsudo systemctl restart sshd"))
    if "PasswordAuthentication yes" in ssh:
        findings.append(("MEDIUM", "SSH password auth enabled",
            "SSH allows password login — vulnerable to brute force",
            "Consider key-based auth:\nsudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"))

    # Check open ports
    ports = data.get("open_ports", "")
    risky = {"23": "Telnet", "21": "FTP", "3389": "RDP", "5900": "VNC"}
    for port, name in risky.items():
        if f":{port} " in ports or f":{port}\n" in ports:
            findings.append(("HIGH", f"Risky port open: {name} :{port}",
                f"{name} is running and exposed",
                f"sudo ufw deny {port}\nsudo systemctl disable {name.lower()} 2>/dev/null || true"))

    # Check rkhunter
    rk = data.get("rkhunter", "")
    if "Warning" in rk or "Found" in rk:
        findings.append(("HIGH", "Rkhunter warnings detected",
            rk[:200],
            "sudo rkhunter --check --nocolors 2>&1 | grep -A2 Warning\nInvestigate each warning manually"))
    else:
        findings.append(("OK", "Rkhunter: Clean", "", ""))

    # Check world-writable /etc files
    writable = data.get("writable_etc", "")
    if writable and writable.strip():
        findings.append(("MEDIUM", "World-writable files in /etc",
            writable[:200],
            "sudo chmod o-w <filename>  # For each file listed"))

    # Check shadow file permissions
    shadow = data.get("shadow_perms", "")
    if shadow and "----------" not in shadow and "640" not in shadow:
        findings.append(("MEDIUM", "Shadow file permissions may be too open",
            shadow,
            "sudo chmod 640 /etc/shadow\nsudo chmod 640 /etc/gshadow"))

    # Check fail2ban
    tools = data.get("security_tools", "")
    if "fail2ban': 'not installed'" in tools:
        findings.append(("MEDIUM", "fail2ban not installed",
            "No brute-force protection on SSH/services",
            "sudo apt install fail2ban\nsudo systemctl enable --now fail2ban"))

    # Build report
    report = [
        "=" * 58,
        "  RIDOS AI Security Scanner — Offline Report",
        "=" * 58, ""
    ]

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "OK": 4}
    findings.sort(key=lambda x: severity_order.get(x[0], 5))

    icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "OK": "🟢"}

    report.append("SECURITY FINDINGS:")
    for sev, title, detail, fix in findings:
        icon = icons.get(sev, "⚪")
        report.append(f"\n  {icon} [{sev}] {title}")
        if detail:
            report.append(f"     {detail[:120]}")
        if fix:
            report.append(f"     Fix:\n     {fix}")

    critical = sum(1 for f in findings if f[0] in ("CRITICAL", "HIGH"))
    report.append(f"\n{'='*58}")
    report.append(f"  Score: {'⚠️  ' + str(critical) + ' high-severity issues found' if critical else '✅ No critical issues found'}")
    report.append(f"  Run 'sudo lynis audit system' for full enterprise audit")

    return "\n".join(report)

def main():
    os.system("clear")
    header("RIDOS AI Security Scanner v1.1.0")
    online = is_online()
    print(f"  Mode: {'🌐 Online AI' if online else '📴 Offline (Local Audit)'}")
    print("  ⚠️  Some checks require sudo\n")

    print("  Options:")
    print("  1. Full security audit")
    print("  2. Quick firewall & ports check")
    print("  3. Rootkit scan (rkhunter)")
    print("  4. Ask a security question")
    print("  5. Exit")

    while True:
        try:
            choice = input("\n  Choice [1-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            print("\n  Running full security audit (may take 60s)...\n")
            data = collect_security_data()
            summary = "\n".join(f"{k}: {str(v)[:300]}" for k, v in data.items())
            response, mode = ask_ai(SYSTEM_PROMPT, f"Security audit data:\n{summary}", offline_security_scanner)
            tag = "🌐" if mode == "online" else "📴"
            print(f"  {tag} Security Report:\n\n{response}")

        elif choice == "2":
            out, _, _ = run_cmd("sudo ufw status")
            print(f"\n  Firewall:\n{out}")
            out, _, _ = run_cmd("sudo ss -tuln")
            print(f"\n  Open ports:\n{out}")

        elif choice == "3":
            print("\n  Running rkhunter scan (may take 2 min)...")
            out, _, rc = run_cmd("sudo rkhunter --check --sk --nocolors 2>/dev/null")
            if rc == 0:
                warnings = [l for l in out.split("\n") if "Warning" in l or "Found" in l]
                if warnings:
                    print(f"  ⚠️  {len(warnings)} warnings found:")
                    for w in warnings:
                        print(f"  🟡 {w}")
                else:
                    print("  ✅ rkhunter: No warnings found")
            else:
                print("  ⚠️  rkhunter not available or requires sudo")

        elif choice == "4":
            try:
                q = input("\n  Your question: ").strip()
                if q:
                    data = collect_security_data()
                    ctx = f"Security context: firewall={data.get('ufw','unknown')[:100]}\nQuestion: {q}"
                    response, mode = ask_ai(SYSTEM_PROMPT, ctx, offline_security_scanner)
                    tag = "🌐" if mode == "online" else "📴"
                    print(f"\n  {tag} Answer:\n\n{response}")
            except (KeyboardInterrupt, EOFError):
                pass

        elif choice == "5":
            break

    print("\n  Goodbye!\n")

if __name__ == "__main__":
    main()
