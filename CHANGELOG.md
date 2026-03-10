# Changelog — RIDOS OS

All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] — 2026-03-XX — "Basra"

### Added
- Debian bookworm base (replaces Alpine Linux)
- BIOS + UEFI dual boot support via grub-mkrescue
- `web_search.py` — CVE lookup, RFC lookup, port database, DuckDuckGo
- `setup_wizard.py` — 6-step first-boot wizard with SSH key generation
- `intent_parser.py` — 15+ IT tool intents (nmap, ping, port scan, etc.)
- XFCE4 desktop environment (lightweight, 512MB RAM compatible)
- GitHub Actions CI/CD — auto-builds ISO on every push
- systemd service for `ridos-daemon`
- UFW firewall enabled by default
- Full legal/copyright framework (GPL v3)

### Changed
- Build system migrated from alpine-make-rootfs to live-build
- AI model updated to `claude-haiku-4-5-20251001`
- GRUB theme redesigned with blue/dark color scheme
- `ridos_shell.py` — added `/tools`, `/network`, `/version` commands

### Security
- API key stored at `/etc/ridos/api.key` (chmod 600)
- SSH root login warning in setup wizard
- UFW default deny incoming on first boot

---

## [1.0.0] — 2026-01-XX — Initial Release

### Added
- Alpine Linux base
- Python AI daemon with Claude API integration
- Basic terminal shell interface
- DuckDuckGo web search
- OpenRC service management
- GRUB bootloader (BIOS only)
