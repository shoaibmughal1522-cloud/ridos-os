#!/bin/bash
# RIDOS GRUB Installer v2
# Runs on LIVE system during Calamares installation

LOG="/tmp/ridos-grub.log"
echo "=== RIDOS GRUB Install $(date) ===" > "$LOG"

# Find Calamares mount point - search /tmp for calamares-root-*
T=""
for d in /tmp/calamares-root-*; do
    if [ -d "$d" ] && [ -d "$d/boot" ] && [ -d "$d/etc" ]; then
        T="$d"
        echo "Found: $T" >> "$LOG"
        break
    fi
done

if [ -z "$T" ]; then
    echo "ERROR: No calamares mount found" >> "$LOG"
    cat "$LOG"
    exit 1
fi

echo "Target: $T" >> "$LOG"

# Find the target DISK (parent of mounted partition)
DISK=$(lsblk -no PKNAME $(findmnt -n -o SOURCE $T) 2>/dev/null)
if [ -z "$DISK" ]; then
    # Fallback: find disk from /proc/mounts
    DEV=$(grep "$T " /proc/mounts | awk '{print $1}' | head -1)
    DISK=$(lsblk -no PKNAME $DEV 2>/dev/null)
fi
if [ -z "$DISK" ]; then
    # Last resort: use sda
    DISK="sda"
fi

echo "Disk: /dev/$DISK" >> "$LOG"

# Mount required filesystems
mount --bind /dev     "$T/dev"     >> "$LOG" 2>&1 || true
mount --bind /dev/pts "$T/dev/pts" >> "$LOG" 2>&1 || true
mount --bind /proc    "$T/proc"    >> "$LOG" 2>&1 || true
mount --bind /sys     "$T/sys"     >> "$LOG" 2>&1 || true

# Install GRUB to correct disk
echo "Running: grub-install /dev/$DISK" >> "$LOG"
chroot "$T" grub-install --target=i386-pc --recheck --force /dev/$DISK >> "$LOG" 2>&1
R=$?
echo "grub-install exit: $R" >> "$LOG"

chroot "$T" update-grub >> "$LOG" 2>&1
echo "update-grub done" >> "$LOG"

# Unmount
umount "$T/sys"     >> "$LOG" 2>&1 || true
umount "$T/proc"    >> "$LOG" 2>&1 || true
umount "$T/dev/pts" >> "$LOG" 2>&1 || true
umount "$T/dev"     >> "$LOG" 2>&1 || true

cat "$LOG"
exit $R
