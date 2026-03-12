#!/usr/bin/env python3
"""Patch live-build scripts for Debian bookworm compatibility."""
import os, re, glob

LB_DIR = "/usr/lib/live/build"
SHARE_DIR = "/usr/share/live"

def patch_file(path, replacements):
    try:
        with open(path, 'r') as f:
            content = f.read()
        original = content
        for old, new in replacements:
            content = content.replace(old, new)
        if content != original:
            with open(path, 'w') as f:
                f.write(content)
            print(f"Patched: {path}")
    except Exception as e:
        print(f"Skip {path}: {e}")

# 1. Replace casper with live-boot everywhere
for pattern in [LB_DIR + "/*", SHARE_DIR + "/build/functions/*.sh"]:
    for f in glob.glob(pattern):
        if os.path.isfile(f):
            patch_file(f, [("casper", "live-boot")])

# 2. Set LB_DERIVATIVE to debian in defaults
defaults = "/usr/share/live/build/functions/defaults.sh"
patch_file(defaults, [
    ("LB_DERIVATIVE:-ubuntu", "LB_DERIVATIVE:-debian"),
    ("LB_DERIVATIVE=ubuntu", "LB_DERIVATIVE=debian"),
    ('LB_DERIVATIVE="ubuntu"', 'LB_DERIVATIVE="debian"'),
])

# 3. Remove ubuntu-only syslinux theme packages from lb_binary_syslinux
syslinux = os.path.join(LB_DIR, "lb_binary_syslinux")
if os.path.exists(syslinux):
    with open(syslinux, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if "syslinux-themes-ubuntu-oneiric" in line or "gfxboot-theme-ubuntu" in line:
            # Replace package install lines with no-ops
            new_lines.append(line
                .replace("syslinux-themes-ubuntu-oneiric", "")
                .replace("gfxboot-theme-ubuntu", ""))
        else:
            new_lines.append(line)
    with open(syslinux, 'w') as f:
        f.writelines(new_lines)
    print(f"Patched syslinux themes in {syslinux}")

print("All live-build patches applied successfully")
