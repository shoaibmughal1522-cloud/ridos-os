# Security Policy — RIDOS OS

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ Active support |
| 1.0.x   | ❌ No longer supported |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security issue in RIDOS OS, report it responsibly:

1. **Email:** [your-security-email@domain.com]
2. **Subject:** `[RIDOS-SECURITY] Brief description`
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Your suggested fix (if any)

We will acknowledge your report within **48 hours** and aim to release
a fix within **14 days** for critical issues.

## Scope

In-scope vulnerabilities:
- RIDOS core Python files (`ridos-core/`)
- Build system scripts (`build-system/`)
- Privilege escalation via RIDOS shell
- API key exposure or leakage

Out of scope:
- Vulnerabilities in upstream packages (Debian, Python, Nmap, etc.)
  — report those to the respective upstream projects
- Issues requiring physical access to the machine
- Social engineering attacks

## Security Tools Notice

RIDOS OS includes network security tools (Nmap, Wireshark, tcpdump, etc.).
These tools are intended for **authorized use only** on networks and systems
you own or have explicit written permission to test.

Unauthorized use of these tools may violate laws in your jurisdiction.
The RIDOS OS project is not responsible for misuse of included tools.
