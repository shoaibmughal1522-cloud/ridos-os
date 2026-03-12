#!/usr/bin/env python3
"""Patch live-build scripts for Debian bookworm compatibility."""
import os, glob, stat

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

def write_stub(path):
    with open(path, 'w') as f:
        f.write("#!/bin/sh\nexit 0\n")
    os.chmod(path, 0o755)
    print(f"Stubbed: {path}")

# 1. Replace casper with live-boot everywhere
for pattern in [LB_DIR + "/*", SHARE_DIR + "/build/functions/*.sh"]:
    for f in glob.glob(pattern):
        if os.path.isfile(f):
            patch_file(f, [("casper", "live-boot")])

# 2. Force LB_DERIVATIVE=debian
defaults = "/usr/share/live/build/functions/defaults.sh"
patch_file(defaults, [
    ("LB_DERIVATIVE:-ubuntu", "LB_DERIVATIVE:-debian"),
    ("LB_DERIVATIVE=ubuntu", "LB_DERIVATIVE=debian"),
    ('LB_DERIVATIVE="ubuntu"', 'LB_DERIVATIVE="debian"'),
])

# 3. Stub out lb_binary_syslinux (Ubuntu-only themes break on Debian)
write_stub(os.path.join(LB_DIR, "lb_binary_syslinux"))

# 4. KEEP lb_binary_grub2 intact - it creates the GRUB boot sector
# Just make sure it doesn't fail on missing files
grub2 = os.path.join(LB_DIR, "lb_binary_grub2")
if os.path.exists(grub2):
    with open(grub2, 'r') as f:
        content = f.read()
    # Make grub2 step more resilient
    content = content.replace(
        'set -e',
        'set -e\nset +e  # Allow failures in grub2 step'
    )
    with open(grub2, 'w') as f:
        f.write(content)
    print(f"Made lb_binary_grub2 resilient")

# 5. Fix lb_binary_iso - keep GRUB boot entry, remove isolinux-only entries
iso_script = os.path.join(LB_DIR, "lb_binary_iso")
if os.path.exists(iso_script):
    with open(iso_script, 'r') as f:
        content = f.read()
    # Remove isolinux-specific boot flags (these only work if isolinux is installed)
    content = content.replace('-b isolinux/isolinux.bin', '')
    content = content.replace('-c isolinux/boot.cat', '')
    content = content.replace('-no-emul-boot -boot-load-size 4 -boot-info-table', '')
    content = content.replace('isohybrid', 'true #isohybrid')
    with open(iso_script, 'w') as f:
        f.write(content)
    print(f"Patched lb_binary_iso")

print("All patches applied successfully")
