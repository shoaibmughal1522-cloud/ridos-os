#!/usr/bin/env python3
"""Write GRUB configuration for RIDOS OS"""

grub_cfg = '''set default=0
set timeout=5

menuentry "RIDOS OS v1.1.0 Baghdad" {
  linux /live/vmlinuz boot=live quiet splash
  initrd /live/initrd
}
menuentry "RIDOS OS (safe mode)" {
  linux /live/vmlinuz boot=live nomodeset
  initrd /live/initrd
}
menuentry "RIDOS OS (debug)" {
  linux /live/vmlinuz boot=live
  initrd /live/initrd
}
'''

with open('iso/boot/grub/grub.cfg', 'w') as f:
    f.write(grub_cfg)

print("GRUB config written")
