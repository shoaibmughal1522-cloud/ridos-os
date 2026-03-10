"""
╔══════════════════════════════════════════════════════════════╗
║  RIDOS OS v1.1 — First Boot Setup Wizard                    ║
║  Copyright (C) 2026 RIDOS OS Project                        ║
║  Licensed under GNU General Public License v3 (GPL-3.0)     ║
║  https://github.com/ridos-os/ridos-os                       ║
╚══════════════════════════════════════════════════════════════╝

Runs once on first boot to configure:
  1. API key (Anthropic Claude)
  2. Network connectivity test
  3. User profile (name, timezone)
  4. Shell theme
  5. SSH key generation (optional)
  6. Security baseline check
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime

# ── Terminal colors ────────────────────────────────────────────
BL  = "\033[34m"   # blue
LBL = "\033[94m"   # light blue
G   = "\033[32m"   # green
Y   = "\033[33m"   # yellow
R   = "\033[31m"   # red
C   = "\033[36m"   # cyan
W   = "\033[97m"   # white
D   = "\033[2m"    # dim
BD  = "\033[1m"    # bold
X   = "\033[0m"    # reset

# ── Paths ──────────────────────────────────────────────────────
API_KEY_FILE  = "/etc/ridos/api.key"
CONFIG_FILE   = "/etc/ridos/config.json"
FLAG_FILE     = "/etc/ridos/.setup_complete"   # exists = already configured
VERSION       = "1.1.0"
CODENAME      = "Baghdad"


# ── Helpers ───────────────────────────────────────────────────
def clear():
    os.system("clear")

def header(title: str, step: int = 0, total: int = 0):
    step_str = f"  Step {step}/{total}" if step else ""
    print(f"\n{LBL}{BD}{'─' * 56}{X}")
    print(f"{LBL}{BD}  {title}{X}{D}{step_str}{X}")
    print(f"{LBL}{BD}{'─' * 56}{X}\n")

def ok(msg: str):
    print(f"  {G}✓{X}  {msg}")

def err(msg: str):
    print(f"  {R}✗{X}  {msg}")

def info(msg: str):
    print(f"  {C}▸{X}  {msg}")

def warn(msg: str):
    print(f"  {Y}⚠{X}  {msg}")

def ask(prompt: str, default: str = "") -> str:
    default_hint = f" [{D}{default}{X}]" if default else ""
    try:
        val = input(f"\n  {LBL}▸{X} {prompt}{default_hint}: ").strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Y}Setup cancelled.{X}")
        sys.exit(0)

def ask_password(prompt: str) -> str:
    import getpass
    try:
        return getpass.getpass(f"\n  {LBL}▸{X} {prompt}: ")
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Y}Setup cancelled.{X}")
        sys.exit(0)

def print_banner():
    clear()
    print(f"""
{LBL}{BD}
  ██████╗ ██╗██████╗  ██████╗ ███████╗
  ██╔══██╗██║██╔══██╗██╔═══██╗██╔════╝
  ██████╔╝██║██║  ██║██║   ██║███████╗
  ██╔══██╗██║██║  ██║██║   ██║╚════██║
  ██║  ██║██║██████╔╝╚██████╔╝███████║
  ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝{X}
  {D}v{VERSION} "{CODENAME}"  —  First Boot Setup Wizard{X}
  {D}Copyright (C) 2026 RIDOS OS Project — GPL v3{X}
""")


def load_config() -> dict:
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def save_api_key(key: str):
    os.makedirs(os.path.dirname(API_KEY_FILE), exist_ok=True)
    with open(API_KEY_FILE, "w") as f:
        f.write(key.strip())
    os.chmod(API_KEY_FILE, 0o600)

def is_configured() -> bool:
    return os.path.exists(FLAG_FILE)

def mark_configured():
    os.makedirs(os.path.dirname(FLAG_FILE), exist_ok=True)
    with open(FLAG_FILE, "w") as f:
        f.write(datetime.now().isoformat())


# ── Step 1 — Welcome ──────────────────────────────────────────
def step_welcome():
    print_banner()
    print(f"  {W}Welcome to RIDOS OS!{X}")
    print(f"""
  RIDOS OS is a Linux distribution built for IT professionals.
  It combines familiar tools (Nmap, Wireshark, SSH, Python...)
  with an AI assistant powered by Anthropic Claude.

  This wizard will configure your system in {BD}6 steps{X}.
  Takes about {D}2–3 minutes{X}.

  {D}Press Enter to begin, or Ctrl+C to exit.{X}""")
    ask("Press Enter to start", "")


# ── Step 2 — API Key ──────────────────────────────────────────
async def step_api_key() -> bool:
    header("Claude API Key Setup", 1, 6)

    print(f"""  RIDOS AI uses Anthropic's Claude to answer your questions.
  You need a {W}free API key{X} to enable this feature.

  {C}How to get your key:{X}
    1. Go to  {LBL}https://console.anthropic.com{X}
    2. Sign up (free)
    3. Go to  {LBL}API Keys{X}  →  {LBL}Create Key{X}
    4. Copy the key — it starts with  {Y}sk-ant-{X}

  {D}You can skip this step and configure it later with: ridos-setup{X}
""")

    for attempt in range(3):
        key = ask(f"Paste your API key (attempt {attempt+1}/3, or press Enter to skip)")

        if not key:
            warn("Skipping API key setup. AI features will be disabled.")
            warn("Run 'ridos-setup' later to configure.")
            return False

        # Basic format validation
        if not key.startswith("sk-ant-") or len(key) < 30:
            err("Invalid format. Key must start with 'sk-ant-' and be at least 30 characters.")
            continue

        # Live validation — make a real API call
        info("Validating key with Anthropic API...")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "hi"}]
                    }
                )
                if r.status_code == 200:
                    save_api_key(key)
                    ok("API key validated and saved!")
                    ok(f"Key stored at: {API_KEY_FILE}  (chmod 600)")
                    return True
                elif r.status_code == 401:
                    err("Invalid API key — authentication failed.")
                elif r.status_code == 429:
                    err("Rate limited. Key may be valid but quota exceeded.")
                else:
                    err(f"API returned status {r.status_code}.")
        except Exception as e:
            err(f"Could not reach Anthropic API: {e}")
            warn("Check your internet connection.")

    warn("API key setup failed after 3 attempts.")
    warn("You can configure it later with: sudo ridos-setup --api-key")
    return False


# ── Step 3 — Network ──────────────────────────────────────────
async def step_network():
    header("Network Configuration", 2, 6)

    # Show current interfaces
    info("Detecting network interfaces...")
    try:
        r = subprocess.run(["ip", "-4", "addr", "show"],
                           capture_output=True, text=True, timeout=5)
        # Parse and display cleanly
        for line in r.stdout.split("\n"):
            if "inet " in line or (": " in line and "lo" not in line and "LOOPBACK" not in line):
                print(f"    {D}{line.strip()}{X}")
    except Exception:
        warn("Could not read network interfaces.")

    print()

    # Internet connectivity
    info("Testing internet connectivity...")
    targets = [
        ("Google DNS",    "8.8.8.8",  53),
        ("Cloudflare DNS","1.1.1.1",  53),
        ("Anthropic API", "api.anthropic.com", 443),
    ]
    import socket
    all_ok = True
    for name, host, port in targets:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda h=host, p=port: socket.create_connection((h, p), timeout=3)
            )
            ok(f"{name} — reachable")
        except Exception:
            err(f"{name} — unreachable")
            all_ok = False

    print()
    if all_ok:
        ok("All connectivity checks passed. RIDOS AI will work online.")
    else:
        warn("Some hosts unreachable. RIDOS will work offline with limited features.")

    # Show IP summary
    try:
        ip = socket.gethostbyname(socket.gethostname())
        info(f"Your IP address: {C}{ip}{X}")
    except Exception:
        pass


# ── Step 4 — User Profile ─────────────────────────────────────
def step_user_profile(cfg: dict):
    header("User Profile", 3, 6)

    name = ask("What should RIDOS call you?", "admin")
    cfg["user_name"] = name

    # Timezone
    print(f"\n  {D}Common timezones:{X}")
    zones = [
        ("UTC",                 "Universal Time"),
        ("America/New_York",    "US Eastern"),
        ("America/Los_Angeles", "US Pacific"),
        ("Europe/London",       "UK"),
        ("Europe/Berlin",       "Central Europe"),
        ("Asia/Baghdad",        "Iraq / Kuwait"),
        ("Asia/Riyadh",         "Saudi Arabia"),
        ("Asia/Dubai",          "UAE"),
        ("Asia/Tokyo",          "Japan"),
        ("Australia/Sydney",    "Australia East"),
    ]
    for i, (tz, label) in enumerate(zones, 1):
        print(f"    {D}{i:2d}.{X} {tz:<30} {D}{label}{X}")

    tz_choice = ask("Enter timezone number or full timezone name", "1")
    if tz_choice.isdigit():
        idx = int(tz_choice) - 1
        timezone = zones[idx][0] if 0 <= idx < len(zones) else "UTC"
    else:
        timezone = tz_choice if tz_choice else "UTC"

    cfg["timezone"] = timezone

    # Set system timezone
    try:
        subprocess.run(["timedatectl", "set-timezone", timezone],
                       capture_output=True, timeout=5)
        ok(f"Timezone set to: {timezone}")
    except Exception:
        warn(f"Could not set timezone automatically. Set manually: timedatectl set-timezone {timezone}")

    ok(f"Welcome, {name}!")
    return cfg


# ── Step 5 — Shell Theme ──────────────────────────────────────
def step_theme(cfg: dict):
    header("Shell Theme", 4, 6)

    themes = {
        "1": ("blue",   BL,  "Classic Blue   — professional, clean"),
        "2": ("green",  G,   "Matrix Green   — hacker aesthetic"),
        "3": ("red",    R,   "Alert Red      — high contrast"),
        "4": ("cyan",   C,   "Cyber Cyan     — modern terminal"),
        "5": ("white",  W,   "Minimal White  — distraction-free"),
    }

    print(f"  Choose your RIDOS shell color theme:\n")
    for key, (name, color, desc) in themes.items():
        bar = f"{color}{'█' * 12}{X}"
        print(f"    {key}. {bar}  {D}{desc}{X}")

    choice = ask("Enter theme number", "1")
    theme_data = themes.get(choice, themes["1"])
    cfg["theme"] = theme_data[0]

    color = theme_data[1]
    ok(f"Theme set to: {color}{theme_data[0].capitalize()}{X}")
    return cfg


# ── Step 6 — SSH Keys ─────────────────────────────────────────
def step_ssh_keys(cfg: dict):
    header("SSH Key Generation", 5, 6)

    print(f"""  SSH keys allow you to authenticate to remote servers
  without passwords — more secure and convenient.

  RIDOS will generate an {W}Ed25519{X} key pair for you.
  {D}(Ed25519 is the modern, recommended algorithm){X}
""")

    generate = ask("Generate SSH key pair? (y/n)", "y").lower()

    if generate != "y":
        warn("Skipping SSH key generation.")
        info("Generate later with: ssh-keygen -t ed25519")
        return cfg

    key_path = os.path.expanduser("~/.ssh/id_ed25519")
    os.makedirs(os.path.expanduser("~/.ssh"), mode=0o700, exist_ok=True)

    if os.path.exists(key_path):
        overwrite = ask("SSH key already exists. Overwrite? (y/n)", "n").lower()
        if overwrite != "y":
            ok("Keeping existing SSH key.")
            info(f"Public key: {key_path}.pub")
            return cfg

    comment = cfg.get("user_name", "ridos") + "@ridos-os"
    try:
        result = subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-C", comment,
             "-f", key_path, "-N", ""],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            ok("SSH Ed25519 key pair generated!")
            ok(f"Private key: {key_path}  (keep this secret!)")
            ok(f"Public key:  {key_path}.pub  (share this with servers)")
            print()
            info("Your public key (copy to authorized_keys on servers):")
            try:
                pub = open(f"{key_path}.pub").read().strip()
                print(f"\n  {C}{pub}{X}\n")
            except Exception:
                pass
            cfg["ssh_key_generated"] = True
        else:
            err(f"Key generation failed: {result.stderr}")
    except FileNotFoundError:
        err("ssh-keygen not found. Install openssh-client.")
    except Exception as e:
        err(f"Error: {e}")

    return cfg


# ── Step 7 — Security Baseline ───────────────────────────────
def step_security(cfg: dict):
    header("Security Baseline Check", 6, 6)

    info("Running quick security checks...")
    print()

    checks = []

    # Check 1 — UFW firewall status
    try:
        r = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=5)
        if "active" in r.stdout.lower():
            checks.append((True, "Firewall (UFW) is active"))
        else:
            checks.append((False, "Firewall (UFW) is inactive — enabling..."))
            subprocess.run(["ufw", "--force", "enable"], capture_output=True, timeout=5)
            subprocess.run(["ufw", "default", "deny", "incoming"], capture_output=True, timeout=5)
            subprocess.run(["ufw", "default", "allow", "outgoing"], capture_output=True, timeout=5)
            subprocess.run(["ufw", "allow", "ssh"], capture_output=True, timeout=5)
            checks.append((True, "Firewall (UFW) enabled with default rules"))
    except Exception:
        checks.append((False, "Could not check firewall status"))

    # Check 2 — Root login via SSH
    try:
        sshd_config = open("/etc/ssh/sshd_config").read()
        if "PermitRootLogin no" in sshd_config:
            checks.append((True, "SSH root login: disabled"))
        else:
            checks.append((False, "SSH root login: not explicitly disabled"))
            info("Recommendation: Add 'PermitRootLogin no' to /etc/ssh/sshd_config")
    except Exception:
        checks.append((None, "SSH config not readable"))

    # Check 3 — Password for ridos user
    try:
        shadow = open("/etc/shadow").read()
        if "ridos:!" in shadow or "ridos:*" in shadow:
            checks.append((False, "User 'ridos' has no password set"))
        else:
            checks.append((True, "User 'ridos' has a password set"))
    except Exception:
        checks.append((None, "Could not read /etc/shadow (need root)"))

    # Check 4 — Automatic updates
    try:
        r = subprocess.run(["dpkg", "-l", "unattended-upgrades"],
                           capture_output=True, text=True, timeout=5)
        if "ii" in r.stdout:
            checks.append((True, "Unattended security upgrades: installed"))
        else:
            checks.append((False, "Unattended upgrades not installed"))
            info("Install with: sudo apt install unattended-upgrades")
    except Exception:
        checks.append((None, "Could not check unattended-upgrades"))

    # Display results
    for status, message in checks:
        if status is True:
            ok(message)
        elif status is False:
            warn(message)
        else:
            info(message)

    cfg["security_check_done"] = True
    cfg["security_check_date"] = datetime.now().isoformat()
    return cfg


# ── Final summary ─────────────────────────────────────────────
def step_complete(cfg: dict):
    clear()
    print_banner()

    ai_status  = G + "ENABLED"  + X if os.path.exists(API_KEY_FILE) and \
                 open(API_KEY_FILE).read().strip() not in ("CONFIGURE_ON_FIRST_BOOT","") \
                 else Y + "DISABLED (no API key)" + X

    print(f"""
{LBL}{BD}  ╔══════════════════════════════════════════╗
  ║     RIDOS OS is Ready!  🎉              ║
  ╚══════════════════════════════════════════╝{X}

  {D}Configuration Summary:{X}

    User Name   :  {W}{cfg.get('user_name', 'admin')}{X}
    Timezone    :  {cfg.get('timezone', 'UTC')}
    Theme       :  {cfg.get('theme', 'blue').capitalize()}
    AI Assistant:  {ai_status}
    SSH Keys    :  {'Generated' if cfg.get('ssh_key_generated') else 'Not generated'}

  {D}Quick Reference:{X}

    Start AI shell  :  {C}ridos-shell{X}
    System status   :  {C}ridos-shell /status{X}
    Reconfigure     :  {C}sudo ridos-setup{X}
    Set API key     :  {C}sudo ridos-setup --api-key{X}
    Network tools   :  {C}nmap, wireshark, tcpdump, ssh{X}

  {D}Copyright (C) 2026 RIDOS OS Project — GPL v3{X}
  {D}https://github.com/ridos-os/ridos-os{X}
""")

    # Count down and launch shell
    for i in range(5, 0, -1):
        print(f"\r  {D}Launching RIDOS shell in {i}s... (Ctrl+C to stay at terminal){X}",
              end="", flush=True)
        time.sleep(1)
    print()


# ── Main ──────────────────────────────────────────────────────
async def run_wizard():
    # Check if already configured (unless --force flag passed)
    if is_configured() and "--force" not in sys.argv and "--reconfigure" not in sys.argv:
        print(f"\n{Y}RIDOS OS is already configured.{X}")
        print(f"Run with {C}--reconfigure{X} to run the wizard again.")
        print(f"Or run {C}ridos-shell{X} to start the AI assistant.\n")
        sys.exit(0)

    cfg = load_config()

    try:
        step_welcome()

        api_ok = await step_api_key()

        await step_network()

        cfg = step_user_profile(cfg)

        cfg = step_theme(cfg)

        cfg = step_ssh_keys(cfg)

        cfg = step_security(cfg)

        # Save final config
        cfg["setup_complete"]  = True
        cfg["setup_date"]      = datetime.now().isoformat()
        cfg["ridos_version"]   = VERSION
        save_config(cfg)
        mark_configured()

        step_complete(cfg)

        # Launch the RIDOS shell
        shell = "/opt/ridos/bin/ridos_shell.py"
        if os.path.exists(shell):
            os.execv(sys.executable, [sys.executable, shell])
        else:
            print(f"{Y}ridos_shell.py not found. Start manually: python3 {shell}{X}")

    except KeyboardInterrupt:
        print(f"\n\n{Y}Setup wizard interrupted.{X}")
        print(f"Run {C}ridos-setup{X} to configure RIDOS OS at any time.\n")
        sys.exit(0)


if __name__ == "__main__":
    # Must run as root for system configuration
    if os.geteuid() != 0 and "--no-root" not in sys.argv:
        print(f"{Y}Note: Running without root. Some steps (firewall, timezone) may fail.{X}")
        print(f"For full setup: {C}sudo python3 setup_wizard.py{X}\n")
    asyncio.run(run_wizard())
