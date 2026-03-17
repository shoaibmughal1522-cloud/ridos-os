#!/usr/bin/env python3
"""
RIDOS AI Hardware Fixer - HDD/SSD/NVMe/RAM diagnostics and repair guidance
Full offline capability using smartmontools, hdparm, nvme-cli, memtester
"""

import sys
import os
import re
sys.path.insert(0, '/opt/ridos/bin')
from ai_engine import ask_ai, is_online, header, status, run_cmd

SYSTEM_PROMPT = """You are RIDOS AI Hardware Fixer. Analyze hardware diagnostic data and:
1. Identify failing or degraded hardware
2. Rate urgency: CRITICAL (replace now) / WARNING (monitor) / OK
3. Give specific repair or mitigation commands
4. Advise on data backup if risk is detected
Be direct about hardware health — people's data is at stake."""

def get_all_disks():
    """Get list of all physical disks."""
    out, _, _ = run_cmd("lsblk -dno NAME,TYPE | grep disk | awk '{print $1}'")
    return [d.strip() for d in out.split("\n") if d.strip()]

def get_disk_smart(disk):
    """Get SMART data for a disk."""
    data = {}
    out, _, rc = run_cmd(f"sudo smartctl -a /dev/{disk} 2>/dev/null")
    if rc == 0 and out:
        data["raw"] = out
        # Parse key attributes
        data["health"] = "PASSED" if "PASSED" in out else ("FAILED" if "FAILED" in out else "UNKNOWN")
        data["type"] = "NVMe" if "NVMe" in out else ("SSD" if "Solid State" in out or "SSD" in out else "HDD")

        # Extract critical SMART attributes
        attrs = {
            "Reallocated_Sector_Ct": "Reallocated sectors",
            "Current_Pending_Sector": "Pending sectors",
            "Offline_Uncorrectable": "Uncorrectable errors",
            "Reported_Uncorrect": "Reported errors",
            "Temperature_Celsius": "Temperature",
            "Power_On_Hours": "Power-on hours",
        }
        for attr, label in attrs.items():
            match = re.search(rf'{attr}.*?(\d+)\s*$', out, re.MULTILINE)
            if match:
                data[label] = match.group(1)
    return data

def get_nvme_health(disk):
    """Get NVMe specific health data."""
    out, _, rc = run_cmd(f"sudo nvme smart-log /dev/{disk} 2>/dev/null")
    if rc == 0:
        return out
    return ""

def get_ram_info():
    """Get RAM information."""
    data = {}
    out, _, _ = run_cmd("sudo dmidecode -t memory 2>/dev/null | grep -E 'Size|Type|Speed|Manufacturer|Part'")
    data["info"] = out
    out, _, _ = run_cmd("free -h")
    data["usage"] = out
    out, _, _ = run_cmd("cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvail|Dirty|Writeback'")
    data["meminfo"] = out
    # Check for memory errors in dmesg
    out, _, _ = run_cmd("dmesg | grep -iE 'memory error|MCE|mce|edac|corrected error' | tail -10")
    data["errors"] = out or "None"
    return data

def offline_hardware_fixer(message):
    """Local hardware diagnosis without AI API."""
    disks = get_all_disks()
    ram = get_ram_info()
    report = [
        "=" * 58,
        "  RIDOS AI Hardware Fixer — Offline Report",
        "=" * 58, ""
    ]

    # Disk analysis
    report.append("STORAGE HEALTH:")
    for disk in disks:
        smart = get_disk_smart(disk)
        health = smart.get("health", "UNKNOWN")
        dtype = smart.get("type", "Disk")
        icon = "🟢" if health == "PASSED" else ("🔴" if health == "FAILED" else "🟡")
        report.append(f"\n  {icon} /dev/{disk} [{dtype}] — SMART: {health}")

        if health == "FAILED":
            report.append("  ⚠️  BACKUP YOUR DATA IMMEDIATELY")
            report.append(f"  sudo smartctl -a /dev/{disk}  # Full details")

        # Check critical attributes
        realloc = int(smart.get("Reallocated sectors", "0") or "0")
        pending = int(smart.get("Pending sectors", "0") or "0")
        uncorrect = int(smart.get("Uncorrectable errors", "0") or "0")
        temp = smart.get("Temperature", "N/A")
        hours = smart.get("Power-on hours", "N/A")

        if realloc > 0:
            report.append(f"  🟡 Reallocated sectors: {realloc} (sign of wear)")
        if pending > 0:
            report.append(f"  🔴 Pending sectors: {pending} (imminent failure risk)")
            report.append(f"  Run: sudo badblocks -n /dev/{disk}  # Check for bad blocks")
        if uncorrect > 0:
            report.append(f"  🔴 Uncorrectable errors: {uncorrect} (data loss risk)")

        if temp != "N/A":
            t = int(temp)
            temp_icon = "🟢" if t < 45 else ("🟡" if t < 55 else "🔴")
            report.append(f"  {temp_icon} Temperature: {t}°C")

        if hours != "N/A":
            h = int(hours)
            age_icon = "🟢" if h < 20000 else ("🟡" if h < 40000 else "🔴")
            report.append(f"  {age_icon} Power-on hours: {h:,} (~{h//8760} years)")

        # NVMe specific
        if "nvme" in disk:
            nvme = get_nvme_health(disk)
            if nvme:
                wear = re.search(r'percentage_used\s*:\s*(\d+)', nvme)
                if wear:
                    w = int(wear.group(1))
                    wear_icon = "🟢" if w < 50 else ("🟡" if w < 80 else "🔴")
                    report.append(f"  {wear_icon} NVMe wear: {w}% used")

    # RAM analysis
    report.append("\nRAM HEALTH:")
    if ram.get("errors") and ram["errors"] != "None":
        report.append(f"  🔴 Memory errors detected in kernel log!")
        report.append(f"  {ram['errors']}")
        report.append("  Run memtest86+ from boot menu to confirm")
    else:
        report.append("  🟢 No memory errors in kernel log")

    report.append(f"\n  Usage:\n{ram.get('usage','N/A')}")

    # Dim info
    report.append(f"\n  Installed RAM:")
    if ram.get("info"):
        for line in ram["info"].split("\n"):
            if line.strip() and "No Module" not in line:
                report.append(f"  {line.strip()}")

    report.append("\nDIAGNOSTIC COMMANDS:")
    report.append("  sudo smartctl -a /dev/sda          # Full SMART report")
    report.append("  sudo nvme smart-log /dev/nvme0      # NVMe health")
    report.append("  sudo memtester 512M 1               # RAM test (needs root)")
    report.append("  memtest86+ from boot menu           # Full RAM test")

    return "\n".join(report)

def main():
    os.system("clear")
    header("RIDOS AI Hardware Fixer v1.1.0")
    online = is_online()
    print(f"  Mode: {'🌐 Online AI' if online else '📴 Offline (Local Diagnostics)'}")

    print("\n  Options:")
    print("  1. Full hardware scan (HDD/SSD/NVMe + RAM)")
    print("  2. Quick disk health check")
    print("  3. RAM information")
    print("  4. Ask a hardware question")
    print("  5. Exit")

    while True:
        try:
            choice = input("\n  Choice [1-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            print("\n  Scanning all hardware (may take 30s)...\n")
            disks = get_all_disks()
            ram = get_ram_info()
            all_smart = {d: get_disk_smart(d) for d in disks}
            summary = f"Disks: {disks}\nSMART: {all_smart}\nRAM: {ram}"
            response, mode = ask_ai(SYSTEM_PROMPT, f"Analyze hardware:\n{summary}", offline_hardware_fixer)
            tag = "🌐" if mode == "online" else "📴"
            print(f"  {tag} Hardware Report:\n\n{response}")

        elif choice == "2":
            disks = get_all_disks()
            print(f"\n  Found disks: {', '.join(disks) or 'none'}\n")
            for disk in disks:
                smart = get_disk_smart(disk)
                health = smart.get("health", "UNKNOWN")
                icon = "✅" if health == "PASSED" else ("❌" if health == "FAILED" else "⚠️")
                print(f"  {icon} /dev/{disk}: SMART {health} | Temp: {smart.get('Temperature','N/A')}°C | Hours: {smart.get('Power-on hours','N/A')}")

        elif choice == "3":
            ram = get_ram_info()
            print(f"\n  RAM Usage:\n{ram.get('usage','N/A')}")
            print(f"\n  RAM Modules:\n{ram.get('info','N/A')}")
            print(f"\n  Kernel memory errors: {ram.get('errors','None')}")

        elif choice == "4":
            try:
                q = input("\n  Your question: ").strip()
                if q:
                    disks = get_all_disks()
                    ctx = f"Disks: {disks}\nQuestion: {q}"
                    response, mode = ask_ai(SYSTEM_PROMPT, ctx, offline_hardware_fixer)
                    tag = "🌐" if mode == "online" else "📴"
                    print(f"\n  {tag} Answer:\n\n{response}")
            except (KeyboardInterrupt, EOFError):
                pass

        elif choice == "5":
            break

    print("\n  Goodbye!\n")

if __name__ == "__main__":
    main()
