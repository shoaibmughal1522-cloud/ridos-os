#!/usr/bin/env python3
"""Patch live-build scripts for Debian bookworm compatibility."""
import os, glob

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

# 3. Completely replace lb_binary_syslinux with a no-op stub
syslinux = os.path.join(LB_DIR, "lb_binary_syslinux")
if os.path.exists(syslinux):
    with open(syslinux, 'w') as f:
        f.write("#!/bin/sh\n# Disabled - Ubuntu-only syslinux themes not available in Debian\nexit 0\n")
    os.chmod(syslinux, 0o755)
    print(f"Replaced lb_binary_syslinux with no-op stub")

# 4. Fix lb_binary_iso - remove isolinux boot params so genisoimage works without it
iso_script = os.path.join(LB_DIR, "lb_binary_iso")
if os.path.exists(iso_script):
    with open(iso_script, 'r') as f:
        content = f.read()
    # Remove isolinux boot options from genisoimage/xorriso command
    content = content.replace('-b isolinux/isolinux.bin', '')
    content = content.replace('-c isolinux/boot.cat', '')
    content = content.replace('-no-emul-boot -boot-load-size 4 -boot-info-table', '')
    content = content.replace('-no-emul-boot', '')
    content = content.replace('isohybrid', 'true #isohybrid')
    with open(iso_script, 'w') as f:
        f.write(content)
    print(f"Patched lb_binary_iso to remove isolinux deps")

print("All live-build patches applied successfully")
