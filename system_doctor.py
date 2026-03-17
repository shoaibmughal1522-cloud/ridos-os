#!/usr/bin/env python3
"""
RIDOS AI System Doctor - Diagnoses system problems and suggests fixes
Offline-first with full local diagnostic capability
"""

import sys
import os
import re
sys.path.insert(0, '/opt/ridos/bin')
from ai_engine import ask_ai, is_online, header, status, run_cmd

SYSTEM_PROMPT = """You are RIDOS AI System Doctor. Analyze system diagnostic data and:
1. Identify problems clearly
2. Explain the cause in simple terms
3. Give exact terminal commands to fix each issue
4. Rate severity: CRITICAL / WARNING / INFO
Be concise and actionable."""

def collect_diagnostics():
    """Collect comprehensive system diagnostic data."""
    diag = {}

    # CPU & load
    out, _, _ = run_cmd("uptime")
    diag["uptime"] = out
    out, _, _ = run_cmd("lscpu | grep -E 'Model name|CPU\(s\)|MHz'")
    diag["cpu"] = out

    # Memory
    out, _, _ = run_cmd("free -h")
    diag["memory"] = out
    out, _, _ = run_cmd("cat /proc/meminfo | grep -E 'MemTotal|MemAvail|SwapTotal|SwapFree'")
    diag["meminfo"] = out

    # Disk health
    out, _, _ = run_cmd("df -h")
    diag["disk_usage"] = out
    out, _, _ = run_cmd("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE")
    diag["block_devices"] = out

    # Failed services
    out, _, _ = run_cmd("systemctl --failed --no-legend 2>/dev/null")
    diag["failed_services"] = out or "None"

    # Recent errors
    out, _, _ = run_cmd("journalctl -b -p err --no-pager -n 20 2>/dev/null")
    diag["boot_errors"] = out or "None"

    # High CPU processes
    out, _, _ = run_cmd("ps aux --sort=-%cpu | head -8")
    diag["top_processes"] = out

    # Temperature
    out, _, _ = run_cmd("sensors 2>/dev/null || echo 'sensors not available'")
    diag["temperature"] = out

    # Network
    out, _, _ = run_cmd("ip a | grep -E 'inet |state'")
    diag["network"] = out

    # Hardware errors
    out, _, _ = run_cmd("dmesg | grep -iE 'error|fail|warn|critical' | tail -15")
    diag["hw_errors"] = out or "None"

    # SMART disk health (first disk)
    disk, _, _ = run_cmd("lsblk -dno NAME | grep -E '^sd|^nvme|^hd' | head -1")
    if disk:
        out, _, _ = run_cmd(f"sudo smartctl -H /dev/{disk} 2>/dev/null")
        diag["smart"] = out or "SMART not available"

    return diag

def offline_doctor(message):
    """Local rule-based system diagnosis."""
    diag = collect_diagnostics()
    issues = []
    fixes = []

    # Check disk usage
    for line in diag.get("disk_usage", "").split("\n"):
        match = re.search(r'(\d+)%\s+(/\S*)', line)
        if match:
            pct, mount = int(match.group(1)), match.group(2)
            if pct >= 90:
                issues.append(f"CRITICAL: Disk {mount} is {pct}% full")
                fixes.append(f"  sudo apt autoremove && sudo apt clean\n  du -sh /* 2>/dev/null | sort -rh | head -10")
            elif pct >= 75:
                issues.append(f"WARNING: Disk {mount} is {pct}% full")

    # Check memory
    mem_line = diag.get("memory", "")
    match = re.search(r'Mem:\s+(\S+)\s+(\S+)\s+(\S+)', mem_line)
    if match:
        total, used, free = match.group(1), match.group(2), match.group(3)
        if 'G' in used and float(used.replace('G','')) / max(float(total.replace('G','1')), 1) > 0.9:
            issues.append(f"WARNING: High memory usage {used}/{total}")
            fixes.append("  sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")

    # Check failed services
    failed = diag.get("failed_services", "None")
    if failed and failed != "None":
        for line in failed.split("\n"):
            if line.strip():
                svc = line.split()[0] if line.split() else "unknown"
                issues.append(f"WARNING: Failed service: {svc}")
                fixes.append(f"  sudo systemctl status {svc}\n  sudo journalctl -u {svc} -n 20")

    # Check boot errors
    errors = diag.get("boot_errors", "None")
    if errors and errors != "None":
        critical = [l for l in errors.split("\n") if "critical" in l.lower() or "error" in l.lower()]
        if critical:
            issues.append(f"WARNING: {len(critical)} boot errors detected")
            fixes.append("  journalctl -b -p err --no-pager | less")

    # Check SMART
    smart = diag.get("smart", "")
    if "FAILED" in smart.upper():
        issues.append("CRITICAL: Disk health check FAILED - backup data immediately!")
        fixes.append("  sudo smartctl -a /dev/sda\n  # Consider replacing the disk")
    elif "PASSED" in smart.upper():
        issues.append("INFO: Disk health PASSED")

    # Build report
    report = ["=" * 55, "  RIDOS AI System Doctor — Offline Report", "=" * 55, ""]
    if issues:
        report.append("FINDINGS:")
        for i in issues:
            icon = "🔴" if "CRITICAL" in i else "🟡" if "WARNING" in i else "🟢"
            report.append(f"  {icon} {i}")
        report.append("\nRECOMMENDED FIXES:")
        for f in fixes:
            report.append(f)
    else:
        report.append("  🟢 System appears healthy — no major issues detected.")

    report.append("\nSYSTEM SNAPSHOT:")
    report.append(f"  Uptime: {diag.get('uptime', 'N/A')}")
    report.append(f"  Memory:\n{diag.get('memory', 'N/A')}")
    return "\n".join(report)

def main():
    os.system("clear")
    header("RIDOS AI System Doctor v1.1.0")
    online = is_online()
    print(f"  Mode: {'🌐 Online AI' if online else '📴 Offline (Local Diagnostics)'}")
    print(f"\n  Collecting system data...\n")

    diag = collect_diagnostics()

    # Show live status
    print("  LIVE SYSTEM STATUS:")
    failed = diag.get("failed_services", "None")
    status("Failed services", "None" if failed == "None" else failed.count("\n")+1, failed == "None")

    disk_ok = all(
        int(m.group(1)) < 85
        for line in diag.get("disk_usage","").split("\n")
        for m in [re.search(r'(\d+)%', line)] if m
    )
    status("Disk usage", "OK" if disk_ok else "High", disk_ok)

    smart_ok = "FAILED" not in diag.get("smart","").upper()
    status("Disk SMART health", "OK" if smart_ok else "FAILED", smart_ok)

    hw_err = diag.get("hw_errors","None")
    status("Hardware errors", "None" if hw_err == "None" else "Errors found", hw_err == "None")

    print("\n  Running full AI diagnosis...\n")
    diag_summary = "\n".join(f"{k}: {v[:200]}" for k, v in diag.items())
    response, mode_used = ask_ai(
        SYSTEM_PROMPT,
        f"Diagnose this system:\n{diag_summary}",
        offline_doctor
    )

    tag = "🌐 AI Analysis" if mode_used == "online" else "📴 Local Analysis"
    print(f"  {tag}:\n")
    print(response)

    print("\n" + "═"*55)
    input("  Press Enter to exit...")

if __name__ == "__main__":
    main()
