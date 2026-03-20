#!/usr/bin/env python3
"""Configure RIDOS OS system settings in chroot"""
import os, subprocess

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Written: {path}")

def run(cmd):
    return subprocess.run(cmd, shell=True)

# Hostname
write('chroot/etc/hostname', 'ridos-os\n')

# hosts
write('chroot/etc/hosts',
    '127.0.0.1 localhost\n'
    '127.0.1.1 ridos-os\n'
    '::1       localhost ip6-localhost ip6-loopback\n')

# locale.gen
write('chroot/etc/locale.gen',
    'en_US.UTF-8 UTF-8\n'
    'ar_IQ.UTF-8 UTF-8\n')

# default locale
write('chroot/etc/default/locale', 'LANG=en_US.UTF-8\n')

# locale-gen
run('chroot chroot locale-gen')

# timezone
run('chroot chroot ln -sf /usr/share/zoneinfo/Asia/Baghdad /etc/localtime')

# Create ridos user
run('chroot chroot useradd -m -s /bin/bash -G sudo,audio,video,netdev,plugdev,bluetooth ridos 2>/dev/null || true')
run('echo "ridos:ridos" | chroot chroot chpasswd')
run('echo "root:ridos" | chroot chroot chpasswd')

# LightDM config
os.makedirs('chroot/etc/lightdm/lightdm.conf.d', exist_ok=True)
write('chroot/etc/lightdm/lightdm.conf.d/50-ridos.conf',
    '[Seat:*]\n'
    'user-session=xfce\n'
    'greeter-session=lightdm-gtk-greeter\n')

write('chroot/etc/lightdm/lightdm-gtk-greeter.conf',
    '[greeter]\n'
    'background=#6B21A8\n'
    'theme-name=Adwaita-dark\n'
    'icon-theme-name=Papirus-Dark\n'
    'font-name=Noto Sans 11\n'
    'indicators=~host;~spacer;~clock;~spacer;~power\n'
    'clock-format=%A, %d %B %Y  %H:%M\n'
    'position=50%,center 50%,center\n')

# os-release
write('chroot/etc/os-release',
    'PRETTY_NAME="RIDOS OS v1.1.0 Baghdad"\n'
    'NAME="RIDOS OS"\n'
    'VERSION_ID="1.1.0"\n'
    'VERSION="1.1.0 (Baghdad)"\n'
    'ID=ridos\n'
    'ID_LIKE=debian\n'
    'HOME_URL="https://github.com/alexeaiskinder-mea/ridos-os"\n'
    'SUPPORT_URL="https://github.com/alexeaiskinder-mea/ridos-os/issues"\n'
    'BUG_REPORT_URL="https://github.com/alexeaiskinder-mea/ridos-os/issues"\n')

# issue
write('chroot/etc/issue',
    'RIDOS OS v1.1.0 Baghdad - AI-Powered Linux\n'
    'Username: ridos | Password: ridos\n')

# Fast shutdown
os.makedirs('chroot/etc/systemd/system.conf.d', exist_ok=True)
write('chroot/etc/systemd/system.conf.d/timeout.conf',
    '[Manager]\n'
    'DefaultTimeoutStopSec=5s\n'
    'DefaultTimeoutStartSec=10s\n'
    'ShutdownWatchdogSec=10s\n')

# Enable services
for svc in ['lightdm','NetworkManager','bluetooth','cups','acpid','ssh','spice-vdagentd','ridos-dashboard']:
    run(f'chroot chroot systemctl enable {svc} 2>/dev/null || true')

print("System configured successfully")
