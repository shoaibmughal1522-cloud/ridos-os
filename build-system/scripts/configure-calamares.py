#!/usr/bin/env python3
"""Configure Calamares installer for RIDOS OS"""
import os, subprocess

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Written: {path}")

def run(cmd):
    return subprocess.run(cmd, shell=True)

os.makedirs('chroot/etc/calamares/branding/ridos', exist_ok=True)
os.makedirs('chroot/etc/calamares/modules', exist_ok=True)

write('chroot/etc/calamares/settings.conf', '''---
modules-search: [ local, /usr/lib/calamares/modules ]

sequence:
  - show:
      - welcome
      - locale
      - keyboard
      - partition
      - users
      - summary
  - exec:
      - partition
      - mount
      - unpackfs
      - machineid
      - fstab
      - locale
      - keyboard
      - users
      - displaymanager
      - packages
      - grubcfg
      - shellprocess
      - bootloader
      - finished

branding: ridos
prompt-install: false
dont-chroot: false
''')

write('chroot/etc/calamares/branding/ridos/branding.desc', '''---
componentName: ridos
welcomeStyleCalamares: true

strings:
  productName: RIDOS OS
  shortProductName: RIDOS
  version: "1.1.0"
  shortVersion: "1.1"
  versionedName: "RIDOS OS 1.1.0"
  shortVersionedName: "RIDOS 1.1"
  bootloaderEntryName: RIDOS
  productUrl: "https://github.com/alexeaiskinder-mea/ridos-os"
  supportUrl: "https://github.com/alexeaiskinder-mea/ridos-os/issues"
  releaseNotesUrl: "https://github.com/alexeaiskinder-mea/ridos-os"

images:
  productLogo: "logo.png"
  productIcon: "logo.png"
  productWelcome: "languages.png"

slideshow: "show.qml"

style:
  sidebarBackground: "#1E1B4B"
  sidebarText: "#FFFFFF"
  sidebarTextSelect: "#6B21A8"
''')

write('chroot/etc/calamares/branding/ridos/show.qml', '''import QtQuick 2.0

Rectangle {
    color: "#1E1B4B"
    width: 800
    height: 500

    Column {
        anchors.centerIn: parent
        spacing: 20

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "RIDOS OS"
            color: "#C4B5FD"
            font.pointSize: 36
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "v1.1.0 Baghdad"
            color: "#E9D5FF"
            font.pointSize: 16
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "AI-Powered Linux for IT Professionals"
            color: "#DDD6FE"
            font.pointSize: 14
        }
    }
}
''')

write('chroot/etc/calamares/modules/partition.conf', '''---
efiSystemPartition: "/boot/efi"
defaultPartitionTableType: gpt
availableFileSystemTypes: [ ext4, btrfs, xfs ]
initialPartitioningChoice: erase
initialSwapChoice: small
''')

write('chroot/etc/calamares/modules/users.conf', '''---
defaultGroups:
  - sudo
  - audio
  - video
  - netdev
  - plugdev
  - bluetooth
  - storage
autologinGroup: autologin
doAutologin: false
sudoersGroup: sudo
setRootPassword: true
passwordRequirements:
  minLength: 6
''')

# Find squashfs path - check multiple locations
write('chroot/etc/calamares/modules/unpackfs.conf', '''---
unpack:
  - source: "/run/live/medium/live/filesystem.squashfs"
    sourcefs: "squashfs"
    destination: ""
  - source: "/lib/live/mount/medium/live/filesystem.squashfs"
    sourcefs: "squashfs"
    destination: ""
''')

write('chroot/etc/calamares/modules/displaymanager.conf', '''---
displaymanagers:
  - lightdm
defaultDesktopEnvironment:
  executable: "startxfce4"
  desktopFile: "xfce.desktop"
basicSetup: false
''')

# locale module config
write('chroot/etc/calamares/modules/locale.conf', '''---
region: "Asia"
zone: "Baghdad"
useSystemTimezone: false
''')

# keyboard module config  
write('chroot/etc/calamares/modules/keyboard.conf', '''---
convertedKeymapPath: "/lib/kbd/keymaps/xkb"
writeEtcDefaultKeyboard: true
''')

# packages module - remove live packages after install
write('chroot/etc/calamares/modules/packages.conf', '''---
backend: apt
update_db: true
operations:
  - remove:
      - live-boot
      - live-boot-initramfs-tools
      - calamares
  - install:
      - grub-pc
      - grub-pc-bin
      - grub2-common
''')

# networkcfg module
write('chroot/etc/calamares/modules/networkcfg.conf', '''---
explicitNMconfig: true
''')

# fstab module - REQUIRED to fix 'No mountOptions' error
write('chroot/etc/calamares/modules/fstab.conf', '''---
mountOptions:
  default: defaults
  btrfs: defaults,noatime,autodefrag
  ext4: defaults,noatime
  fat32: defaults,umask=0077
  vfat: defaults,umask=0077

ssdExtraMountOptions:
  ext4: discard
  btrfs: discard,ssd

efiMountOptions: umask=0077

ensureSuspendToDisk: true
neverCheckSuspendToDisk: false
'''  )

write('chroot/etc/calamares/modules/bootloader.conf', '''---
efiBootLoader: "grub"
grubInstall: "grub-install"
grubMkconfig: "update-grub"
grubCfg: "/boot/grub/grub.cfg"
grubProbe: "grub-probe"
efiInstallerPath: "/usr/bin/efibootmgr"
installEFIFallback: false
canBeSkipped: true
''')

write('chroot/etc/default/grub',
    'GRUB_DEFAULT=0\n'
    'GRUB_TIMEOUT=5\n'
    'GRUB_DISTRIBUTOR="RIDOS OS"\n'
    'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\n'
    'GRUB_CMDLINE_LINUX=""\n')

# Generate logo
run('convert -size 200x200 gradient:"#6B21A8-#1E1B4B" '
    '-font DejaVu-Sans-Bold -pointsize 32 '
    '-fill white -gravity center -annotate 0 "RIDOS" '
    'chroot/etc/calamares/branding/ridos/logo.png 2>/dev/null || '
    'convert -size 200x200 xc:"#6B21A8" '
    '-fill white -gravity center -annotate 0 "RIDOS" '
    'chroot/etc/calamares/branding/ridos/logo.png 2>/dev/null || true')

run('cp chroot/etc/calamares/branding/ridos/logo.png '
    'chroot/etc/calamares/branding/ridos/languages.png 2>/dev/null || true')

# Add shellprocess module - manual GRUB install as reliable fallback
import os
os.makedirs('chroot/etc/calamares/modules', exist_ok=True)

# Create grub-install wrapper script that handles mounting
write('chroot/usr/local/bin/ridos-grub-install', '''#!/bin/bash
# RIDOS GRUB installer
# Calamares 3.2 uses /tmp/calamares-root as mount point

# Log everything
exec >> /tmp/ridos-grub-install.log 2>&1
echo "=== RIDOS GRUB Install started ==="
echo "Date: $(date)"

# Show all current mounts for debugging
echo "=== Current mounts ==="
mount | grep -v "^cgroup\|^sysfs\|^proc\|^tmpfs\|^devpts\|^mqueue\|^hugetlb"

# Find target - check ALL possible locations
TARGET=""

# Method 1: Calamares 3.2 uses /tmp/calamares-root-XXXXXXXX
TARGET=$(ls -d /tmp/calamares-root-* 2>/dev/null | head -1)
if [ -n "$TARGET" ] && [ -d "$TARGET/boot" ]; then
    echo "Found Calamares root: $TARGET"
fi

# Also check plain path
if [ -z "$TARGET" ]; then
    for path in /tmp/calamares-root /tmp/calamares_root /mnt/calamares /mnt; do
        if mountpoint -q "$path" 2>/dev/null && [ -d "$path/boot" ]; then
            TARGET="$path"
            echo "Found via standard path: $TARGET"
            break
        fi
    done
fi

# Method 2: scan all mounts for a Linux root
if [ -z "$TARGET" ]; then
    while IFS= read -r line; do
        mnt=$(echo "$line" | awk "{print \$2}")
        if [ -d "$mnt/boot" ] && [ -d "$mnt/etc" ] && [ -d "$mnt/bin" ]; then
            if [ "$mnt" != "/" ]; then
                TARGET="$mnt"
                echo "Found via mount scan: $TARGET"
                break
            fi
        fi
    done < /proc/mounts
fi

# Method 3: find from /dev/sda1
if [ -z "$TARGET" ]; then
    mkdir -p /mnt/ridos-target
    mount /dev/sda1 /mnt/ridos-target 2>/dev/null
    if [ -d "/mnt/ridos-target/boot" ]; then
        TARGET="/mnt/ridos-target"
        echo "Mounted /dev/sda1 manually: $TARGET"
    fi
fi

echo "Target found: $TARGET"

if [ -z "$TARGET" ]; then
    echo "FATAL: Cannot find target mount point"
    echo "Available mounts:"
    cat /proc/mounts
    exit 1
fi

# Mount required filesystems
echo "Mounting /dev /proc /sys..."
mount --bind /dev     "$TARGET/dev"     2>/dev/null || true
mount --bind /dev/pts "$TARGET/dev/pts" 2>/dev/null || true
mount --bind /proc    "$TARGET/proc"    2>/dev/null || true
mount --bind /sys     "$TARGET/sys"     2>/dev/null || true

# Verify /dev is mounted
if [ ! -e "$TARGET/dev/sda" ]; then
    echo "WARNING: /dev/sda not visible in target, trying udev..."
    udevadm trigger 2>/dev/null || true
    sleep 1
fi

echo "Running grub-install..."
chroot "$TARGET" grub-install --target=i386-pc --recheck --force /dev/sda
RESULT=$?
echo "grub-install exit code: $RESULT"

echo "Running update-grub..."
chroot "$TARGET" update-grub
echo "update-grub exit code: $?"

# Unmount
umount "$TARGET/sys"     2>/dev/null || true
umount "$TARGET/proc"    2>/dev/null || true
umount "$TARGET/dev/pts" 2>/dev/null || true
umount "$TARGET/dev"     2>/dev/null || true

echo "=== RIDOS GRUB Install finished with code $RESULT ==="
exit $RESULT
''')

import subprocess
subprocess.run('chmod +x chroot/usr/local/bin/ridos-grub-install', shell=True)
print("GRUB install script created")

write('chroot/etc/calamares/modules/shellprocess.conf', '''---
dontChroot: true
timeout: 180
verbose: true

script:
  - command: "/usr/local/bin/ridos-grub-install"
    timeout: 180
''')

# Remove calamares-settings-debian which overrides our config
import subprocess
subprocess.run('chroot chroot apt-get remove -y calamares-settings-debian 2>/dev/null || true', shell=True)
print("Removed calamares-settings-debian to prevent config override")

# Create debug launcher script
with open('chroot/usr/local/bin/calamares-debug', 'w') as f:
    f.write('#!/bin/bash\n')
    f.write('calamares -D 8 2>&1 | tee /tmp/calamares-debug.log\n')
    f.write('echo "Log saved to /tmp/calamares-debug.log"\n')
subprocess.run('chmod +x chroot/usr/local/bin/calamares-debug', shell=True)

if os.path.exists('chroot/usr/bin/calamares'):
    print("Calamares installed and configured successfully")
else:
    print("WARNING: Calamares binary not found - config written but installer unavailable")
