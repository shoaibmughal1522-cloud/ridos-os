#!/usr/bin/env python3
"""Apply RIDOS OS branding, theme, and desktop shortcuts"""
import os, subprocess

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def run(cmd):
    return subprocess.run(cmd, shell=True)

# XFCE config dirs
os.makedirs('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml', exist_ok=True)
os.makedirs('chroot/home/ridos/.config/xfce4/terminal', exist_ok=True)
os.makedirs('chroot/home/ridos/Desktop', exist_ok=True)
os.makedirs('chroot/home/ridos/.config/autostart', exist_ok=True)
os.makedirs('chroot/home/ridos/.config/neofetch', exist_ok=True)
os.makedirs('chroot/usr/share/plymouth/themes/ridos', exist_ok=True)

# Dark theme
write('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Net" type="empty">
    <property name="ThemeName" type="string" value="Adwaita-dark"/>
    <property name="IconThemeName" type="string" value="Papirus-Dark"/>
  </property>
  <property name="Gtk" type="empty">
    <property name="FontName" type="string" value="Noto Sans 10"/>
    <property name="MonospaceFontName" type="string" value="Noto Mono 10"/>
    <property name="CursorThemeName" type="string" value="Adwaita"/>
  </property>
</channel>
''')

# Wallpaper
write('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitorVirtual1" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/ridos/ridos-wallpaper.png"/>
        </property>
      </property>
    </property>
  </property>
</channel>
''')

# Window manager
write('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="Default-dark"/>
    <property name="title_font" type="string" value="Noto Sans Bold 10"/>
  </property>
</channel>
''')

# Terminal colors
write('chroot/home/ridos/.config/xfce4/terminal/terminalrc',
    '[Configuration]\n'
    'ColorForeground=#E9D5FF\n'
    'ColorBackground=#0F0A1E\n'
    'ColorCursor=#7C3AED\n'
    'FontName=Noto Mono 11\n')

# XFCE helpers
write('chroot/home/ridos/.config/xfce4/helpers.rc', 'TerminalEmulator=xfce4-terminal\n')

# Desktop shortcuts
desktops = {
    '01-ridos-dashboard.desktop': (
        '[Desktop Entry]\nVersion=1.0\nType=Application\n'
        'Name=RIDOS Dashboard\nComment=RIDOS OS Control Center\n'
        'Exec=firefox-esr /opt/ridos/bin/ridos-dashboard.html\n'
        'Icon=/usr/share/ridos/ridos-icon.png\nTerminal=false\nCategories=System;\n'),
    '02-ridos-ai-tools.desktop': (
        '[Desktop Entry]\nVersion=1.0\nType=Application\n'
        'Name=RIDOS AI Tools\nComment=AI Shell, Network, Hardware, Security\n'
        'Exec=xfce4-terminal --title="RIDOS AI Tools" -e "python3 /opt/ridos/bin/ai_features.py"\n'
        'Icon=utilities-system-monitor\nTerminal=false\nCategories=System;Network;\n'),
    '03-firefox.desktop': (
        '[Desktop Entry]\nVersion=1.0\nType=Application\n'
        'Name=Firefox Browser\nExec=firefox-esr %u\n'
        'Icon=firefox-esr\nTerminal=false\nCategories=Network;WebBrowser;\n'),
    '04-files.desktop': (
        '[Desktop Entry]\nVersion=1.0\nType=Application\n'
        'Name=File Manager\nExec=thunar\n'
        'Icon=system-file-manager\nTerminal=false\nCategories=System;FileManager;\n'),
    '05-terminal.desktop': (
        '[Desktop Entry]\nVersion=1.0\nType=Application\n'
        'Name=Terminal\nExec=xfce4-terminal\n'
        'Icon=utilities-terminal\nTerminal=false\nCategories=System;\n'),
    '06-install-ridos.desktop': (
        '[Desktop Entry]\nVersion=1.0\nType=Application\n'
        'Name=Install RIDOS OS\nComment=Install RIDOS OS to hard drive\n'
        'Exec=bash -c "if [ -f /usr/bin/calamares ]; then pkexec /usr/bin/calamares; '
        'else xfce4-terminal --title=\'RIDOS Installer\' -e \'sudo /opt/ridos/bin/ridos-install.sh\'; fi"\n'
        'Icon=drive-harddisk\nTerminal=false\nCategories=System;\n'),
}

for name, content in desktops.items():
    write(f'chroot/home/ridos/Desktop/{name}', content)
    run(f'chmod +x chroot/home/ridos/Desktop/{name}')

# Plymouth
write('chroot/usr/share/plymouth/themes/ridos/ridos.plymouth',
    '[Plymouth Theme]\n'
    'Name=RIDOS OS\n'
    'Description=RIDOS OS Boot Splash\n'
    'ModuleName=script\n\n'
    '[script]\n'
    'ImageDir=/usr/share/plymouth/themes/ridos\n'
    'ScriptFile=/usr/share/plymouth/themes/ridos/ridos.script\n')

write('chroot/usr/share/plymouth/themes/ridos/ridos.script',
    'Window.SetBackgroundTopColor(0.42, 0.13, 0.66);\n'
    'Window.SetBackgroundBottomColor(0.12, 0.07, 0.27);\n'
    'message_sprite = Sprite();\n'
    'message_sprite.SetPosition(Window.GetWidth()/2 - 150, Window.GetHeight()/2 - 20, 10000);\n'
    'fun refresh_callback() {\n'
    '  message_image = Image.Text("RIDOS OS v1.1.0 Baghdad", 1.0, 1.0, 1.0);\n'
    '  message_sprite.SetImage(message_image);\n'
    '}\n'
    'Plymouth.SetRefreshFunction(refresh_callback);\n')

# Autostart
write('chroot/home/ridos/.config/autostart/ridos-welcome.desktop',
    '[Desktop Entry]\nType=Application\nName=RIDOS Welcome\n'
    'Exec=xfce4-terminal --title="RIDOS OS v1.1.0 Baghdad" -e "bash -c \'cat /etc/motd; echo; bash\'"\n'
    'Hidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\n')

# Neofetch
write('chroot/home/ridos/.config/neofetch/config.conf',
    'print_info() {\n'
    '    info title\n'
    '    info "OS" distro\n'
    '    info "Kernel" kernel\n'
    '    info "Uptime" uptime\n'
    '    info "DE" de\n'
    '    info "CPU" cpu\n'
    '    info "Memory" memory\n'
    '}\n'
    'ascii_distro="auto"\n')

run('chroot chroot chown -R ridos:ridos /home/ridos')
print("Branding applied successfully")
