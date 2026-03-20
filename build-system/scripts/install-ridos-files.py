#!/usr/bin/env python3
"""Install RIDOS core files, wallpaper, installer, and motd"""
import os, subprocess

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def run(cmd):
    return subprocess.run(cmd, shell=True)

# Generate wallpaper
run('convert -size 1920x1080 gradient:"#0F0A1E-#2D1B69" '
    '-fill "rgba(196,181,253,0.15)" -font DejaVu-Sans-Bold '
    '-pointsize 80 -gravity center -annotate 0 "RIDOS OS" '
    'chroot/usr/share/ridos/ridos-wallpaper.png 2>/dev/null || '
    'cp build-system/scripts/ridos-wallpaper.png '
    'chroot/usr/share/ridos/ridos-wallpaper.png 2>/dev/null || true')

# Generate icon
run('convert -size 256x256 gradient:"#6B21A8-#1E1B4B" '
    '-font DejaVu-Sans-Bold -pointsize 48 '
    '-fill white -gravity center -annotate 0 "RIDOS" '
    'chroot/usr/share/ridos/ridos-icon.png 2>/dev/null || true')

# Dashboard service
write('chroot/etc/systemd/system/ridos-dashboard.service',
    '[Unit]\n'
    'Description=RIDOS Dashboard Stats Server\n'
    'After=network.target\n\n'
    '[Service]\n'
    'Type=simple\n'
    'User=ridos\n'
    'ExecStart=/usr/bin/python3 /opt/ridos/bin/dashboard_server.py\n'
    'Restart=always\n'
    'RestartSec=3\n\n'
    '[Install]\n'
    'WantedBy=multi-user.target\n')

# MOTD banner
write('chroot/etc/motd', '''
  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557
  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d
  \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557
  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551
  \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551
  \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d

  RIDOS OS v1.1.0 "Baghdad"
  AI-Powered Linux for IT Professionals
  Username: ridos  |  Password: ridos
  AI Shell: python3 /opt/ridos/bin/ridos_shell.py

''')

# HDD bash installer
write('chroot/opt/ridos/bin/ridos-install.sh', '''#!/bin/bash
clear
echo "============================================"
echo "   RIDOS OS v1.1.0 Baghdad - HDD Installer"
echo "============================================"
echo ""
echo "Available disks:"
lsblk -d -o NAME,SIZE,MODEL | grep -v loop
echo ""
read -p "Enter disk to install to (e.g. sda, sdb): " DISK
DISK="/dev/$DISK"
if [ ! -b "$DISK" ]; then
  echo "ERROR: Disk $DISK not found!"
  read -p "Press Enter to exit..."; exit 1
fi
echo ""; echo "Selected: $DISK"; lsblk "$DISK"; echo ""
read -p "ARE YOU SURE? All data will be ERASED! Type YES: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
  echo "Cancelled."; read -p "Press Enter..."; exit 0
fi
echo "Partitioning..."
parted -s "$DISK" mklabel msdos
parted -s "$DISK" mkpart primary ext4 1MiB 100%
parted -s "$DISK" set 1 boot on
PARTITION="${DISK}1"; sleep 2
echo "Formatting..."; mkfs.ext4 -F "$PARTITION"
mkdir -p /mnt/ridos-install
mount "$PARTITION" /mnt/ridos-install
echo "Copying files (10-20 minutes)..."
rsync -ax --exclude=/proc --exclude=/sys --exclude=/dev \\
  --exclude=/run --exclude=/mnt --exclude=/media \\
  / /mnt/ridos-install/
mkdir -p /mnt/ridos-install/{proc,sys,dev,run,mnt,media}
echo "Installing GRUB..."
mount --bind /dev  /mnt/ridos-install/dev
mount --bind /proc /mnt/ridos-install/proc
mount --bind /sys  /mnt/ridos-install/sys
UUID=$(blkid -s UUID -o value "$PARTITION")
echo "UUID=$UUID / ext4 errors=remount-ro 0 1" > /mnt/ridos-install/etc/fstab
chroot /mnt/ridos-install apt-get remove -y live-boot live-boot-initramfs-tools 2>/dev/null || true
chroot /mnt/ridos-install update-initramfs -u 2>/dev/null || true
chroot /mnt/ridos-install grub-install "$DISK"
chroot /mnt/ridos-install update-grub
sed -i "s/boot=live //" /mnt/ridos-install/boot/grub/grub.cfg 2>/dev/null || true
umount /mnt/ridos-install/sys /mnt/ridos-install/proc /mnt/ridos-install/dev
umount /mnt/ridos-install
echo ""
echo "RIDOS OS installed! Remove USB and reboot."
read -p "Press Enter to exit..."
''')
run('chmod +x chroot/opt/ridos/bin/ridos-install.sh')
run('chroot chroot chown -R ridos:ridos /home/ridos 2>/dev/null || true')
print("RIDOS files installed successfully")
