#!/usr/bin/env python3
"""
RIDOS OS GUI Installer - Install RIDOS OS to HDD/SSD/NVMe
Uses tkinter (no extra dependencies) with a clean step-by-step wizard
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys
import re

# ── Colors matching RIDOS dark purple theme ──
BG       = "#1a0a2e"
BG2      = "#2d1254"
ACCENT   = "#6B21A8"
ACCENT2  = "#9333ea"
FG       = "#ffffff"
FG2      = "#c4b5fd"
GREEN    = "#22c55e"
RED      = "#ef4444"
YELLOW   = "#eab308"
FONT     = ("Noto Sans", 11)
FONT_B   = ("Noto Sans", 11, "bold")
FONT_LG  = ("Noto Sans", 16, "bold")
FONT_SM  = ("Noto Sans", 9)

def run(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "Timed out", 1

def get_disks():
    """Get available physical disks with details."""
    out, _, _ = run("lsblk -dno NAME,SIZE,MODEL,TYPE | grep disk")
    disks = []
    for line in out.split("\n"):
        if line.strip():
            parts = line.split(None, 3)
            if len(parts) >= 2:
                disks.append({
                    "name": parts[0],
                    "size": parts[1],
                    "model": parts[3].strip() if len(parts) > 3 else "Unknown",
                    "path": f"/dev/{parts[0]}"
                })
    return disks

class RIDOSInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RIDOS OS Installer v1.1.0 Baghdad")
        self.geometry("700x520")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.selected_disk = tk.StringVar()
        self.step = 0
        self.log_lines = []
        self._build_ui()
        self._show_welcome()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT, height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  RIDOS OS Installer", font=FONT_LG,
                 bg=ACCENT, fg=FG).pack(side=tk.LEFT, padx=20, pady=15)
        self.step_label = tk.Label(hdr, text="Step 1 of 4", font=FONT_SM,
                                    bg=ACCENT, fg=FG2)
        self.step_label.pack(side=tk.RIGHT, padx=20)

        # Progress bar
        self.progress = ttk.Progressbar(self, length=700, mode='determinate')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", background=ACCENT2, troughcolor=BG2, thickness=6)
        self.progress.pack(fill=tk.X)

        # Main content frame
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Bottom buttons
        btn_frame = tk.Frame(self, bg=BG2, height=60)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        btn_frame.pack_propagate(False)

        self.btn_back = tk.Button(btn_frame, text="◀  Back", font=FONT_B,
                                   bg=BG, fg=FG2, bd=0, padx=20, pady=12,
                                   cursor="hand2", command=self._back)
        self.btn_back.pack(side=tk.LEFT, padx=20, pady=10)

        self.btn_next = tk.Button(btn_frame, text="Next  ▶", font=FONT_B,
                                   bg=ACCENT, fg=FG, bd=0, padx=20, pady=12,
                                   cursor="hand2", command=self._next,
                                   activebackground=ACCENT2, activeforeground=FG)
        self.btn_next.pack(side=tk.RIGHT, padx=20, pady=10)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _label(self, text, font=FONT, fg=FG, pady=4):
        tk.Label(self.content, text=text, font=font, bg=BG, fg=fg,
                 justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=pady)

    # ── Step 0: Welcome ──
    def _show_welcome(self):
        self._clear()
        self.step = 0
        self.step_label.config(text="Step 1 of 4")
        self.progress['value'] = 0
        self.btn_back.config(state=tk.DISABLED)

        self._label("Welcome to RIDOS OS Installer", font=FONT_LG, pady=10)
        self._label("This wizard will install RIDOS OS permanently to your computer.", fg=FG2)
        self._label("")

        warn_frame = tk.Frame(self.content, bg=BG2, padx=15, pady=12)
        warn_frame.pack(fill=tk.X, pady=10)
        tk.Label(warn_frame, text="⚠️  Warning", font=FONT_B, bg=BG2, fg=YELLOW).pack(anchor="w")
        tk.Label(warn_frame,
                 text="Installation will ERASE all data on the selected disk.\nMake sure you have backed up any important files before continuing.",
                 font=FONT, bg=BG2, fg=FG2, justify=tk.LEFT).pack(anchor="w")

        self._label("")
        self._label("Requirements:", font=FONT_B)
        self._label("  ✅  At least 8 GB free disk space", fg=FG2)
        self._label("  ✅  Running from a live USB (RIDOS OS)", fg=FG2)
        self._label("  ✅  Target disk is not the boot USB", fg=FG2)

    # ── Step 1: Disk selection ──
    def _show_disk_select(self):
        self._clear()
        self.step = 1
        self.step_label.config(text="Step 2 of 4")
        self.progress['value'] = 25
        self.btn_back.config(state=tk.NORMAL)

        self._label("Select Installation Disk", font=FONT_LG, pady=10)
        self._label("Choose the disk to install RIDOS OS on:", fg=FG2)
        self._label("⚠️  All data on the selected disk will be erased!", fg=YELLOW)
        self._label("")

        disks = get_disks()
        if not disks:
            self._label("❌ No disks found. Cannot continue.", fg=RED)
            self.btn_next.config(state=tk.DISABLED)
            return

        for disk in disks:
            frame = tk.Frame(self.content, bg=BG2, padx=15, pady=10)
            frame.pack(fill=tk.X, pady=4)
            rb = tk.Radiobutton(
                frame,
                text=f"  {disk['path']}   [{disk['size']}]   {disk['model']}",
                variable=self.selected_disk,
                value=disk['path'],
                font=FONT, bg=BG2, fg=FG,
                selectcolor=ACCENT,
                activebackground=BG2,
                cursor="hand2"
            )
            rb.pack(anchor="w")

        if disks:
            self.selected_disk.set(disks[0]['path'])

    # ── Step 2: Confirm ──
    def _show_confirm(self):
        self._clear()
        self.step = 2
        self.step_label.config(text="Step 3 of 4")
        self.progress['value'] = 50

        disk = self.selected_disk.get()
        self._label("Confirm Installation", font=FONT_LG, pady=10)
        self._label("Please review before proceeding:", fg=FG2)
        self._label("")

        info_frame = tk.Frame(self.content, bg=BG2, padx=20, pady=15)
        info_frame.pack(fill=tk.X, pady=10)

        # Get disk details
        out, _, _ = run(f"lsblk {disk} -o NAME,SIZE,MODEL --nodeps")
        tk.Label(info_frame, text="Installation target:", font=FONT_B, bg=BG2, fg=FG2).pack(anchor="w")
        tk.Label(info_frame, text=f"  {out}", font=FONT, bg=BG2, fg=FG).pack(anchor="w")

        tk.Label(info_frame, text="\nInstall actions:", font=FONT_B, bg=BG2, fg=FG2).pack(anchor="w")
        steps = [
            f"  1. Erase and partition {disk}",
            f"  2. Format as ext4",
            f"  3. Copy RIDOS OS files",
            f"  4. Install GRUB bootloader",
            f"  5. Configure for standalone boot",
        ]
        for s in steps:
            tk.Label(info_frame, text=s, font=FONT, bg=BG2, fg=FG).pack(anchor="w")

        self._label("")
        warn = tk.Frame(self.content, bg="#3b0a0a", padx=15, pady=10)
        warn.pack(fill=tk.X)
        tk.Label(warn, text=f"🔴  ALL DATA ON {disk} WILL BE PERMANENTLY ERASED",
                 font=FONT_B, bg="#3b0a0a", fg=RED).pack(anchor="w")

    # ── Step 3: Installing ──
    def _show_install(self):
        self._clear()
        self.step = 3
        self.step_label.config(text="Step 4 of 4")
        self.progress['value'] = 75
        self.btn_next.config(state=tk.DISABLED)
        self.btn_back.config(state=tk.DISABLED)

        self._label("Installing RIDOS OS...", font=FONT_LG, pady=10)
        self._label("Please wait. Do not remove the USB drive.", fg=FG2)
        self._label("")

        self.install_status = tk.Label(self.content, text="Preparing...",
                                        font=FONT_B, bg=BG, fg=ACCENT2)
        self.install_status.pack(anchor="w", pady=5)

        self.install_progress = ttk.Progressbar(self.content, length=640,
                                                  mode='indeterminate')
        self.install_progress.pack(fill=tk.X, pady=5)
        self.install_progress.start(15)

        # Log area
        log_frame = tk.Frame(self.content, bg="#000000")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_text = tk.Text(log_frame, bg="#000000", fg="#00ff00",
                                 font=("Noto Mono", 9), height=10,
                                 state=tk.DISABLED, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Start install in background thread
        thread = threading.Thread(target=self._do_install, daemon=True)
        thread.start()

    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()

    def _do_install(self):
        disk = self.selected_disk.get()
        steps = [
            ("Partitioning disk...",
             f"sudo parted -s {disk} mklabel msdos && "
             f"sudo parted -s {disk} mkpart primary ext4 1MiB 100% && "
             f"sudo parted -s {disk} set 1 boot on"),
            ("Waiting for partition...", "sleep 3"),
            ("Formatting ext4...", f"sudo mkfs.ext4 -F {disk}1"),
            ("Mounting partition...",
             "sudo mkdir -p /mnt/ridos-install && sudo mount {disk}1 /mnt/ridos-install".format(disk=disk)),
            ("Copying RIDOS OS (10-20 min)...",
             "sudo rsync -ax --info=progress2 "
             "--exclude=/proc --exclude=/sys --exclude=/dev "
             "--exclude=/run --exclude=/mnt --exclude=/media "
             "/ /mnt/ridos-install/"),
            ("Creating system dirs...",
             "sudo mkdir -p /mnt/ridos-install/{proc,sys,dev,run,mnt,media}"),
            ("Binding filesystems...",
             "sudo mount --bind /dev /mnt/ridos-install/dev && "
             "sudo mount --bind /proc /mnt/ridos-install/proc && "
             "sudo mount --bind /sys /mnt/ridos-install/sys"),
            ("Writing fstab...",
             f"UUID=$(sudo blkid -s UUID -o value {disk}1) && "
             "echo \"UUID=$UUID / ext4 errors=remount-ro 0 1\" | sudo tee /mnt/ridos-install/etc/fstab"),
            ("Removing live-boot...",
             "sudo chroot /mnt/ridos-install apt-get remove -y live-boot live-boot-initramfs-tools 2>/dev/null || true"),
            ("Updating initramfs...",
             "sudo chroot /mnt/ridos-install update-initramfs -u 2>/dev/null || true"),
            ("Installing GRUB bootloader...",
             f"sudo chroot /mnt/ridos-install grub-install {disk}"),
            ("Updating GRUB config...",
             "sudo chroot /mnt/ridos-install update-grub"),
            ("Removing live params from GRUB...",
             "sudo sed -i 's/boot=live //g' /mnt/ridos-install/boot/grub/grub.cfg 2>/dev/null || true"),
            ("Unmounting...",
             "sudo umount /mnt/ridos-install/sys /mnt/ridos-install/proc "
             "/mnt/ridos-install/dev /mnt/ridos-install 2>/dev/null || true"),
        ]

        success = True
        for label, cmd in steps:
            self.install_status.config(text=label)
            self._log(f"▶ {label}")
            out, err, rc = run(cmd, timeout=1200)
            if out:
                self._log(f"  {out[:200]}")
            if rc != 0 and "Removing" not in label and "Waiting" not in label:
                self._log(f"  ⚠ {err[:200]}")
                if rc != 0 and any(k in label for k in ["Partition", "Format", "GRUB"]):
                    success = False
                    self._log(f"  ❌ FAILED: {label}")
                    break

        self.install_progress.stop()
        self.progress['value'] = 100

        if success:
            self.install_status.config(text="✅  Installation complete!", fg=GREEN)
            self._log("\n✅ RIDOS OS installed successfully!")
            self._log("Remove the USB drive and reboot.")
            self.btn_next.config(state=tk.NORMAL, text="Finish", command=self._finish)
        else:
            self.install_status.config(text="❌  Installation failed", fg=RED)
            self._log("\n❌ Installation failed. Check the log above.")
            self.btn_back.config(state=tk.NORMAL)

    def _finish(self):
        if messagebox.askyesno("Reboot", "Installation complete!\n\nReboot now?"):
            run("sudo reboot")
        else:
            self.destroy()

    def _next(self):
        if self.step == 0:
            self._show_disk_select()
        elif self.step == 1:
            if not self.selected_disk.get():
                messagebox.showwarning("No disk selected", "Please select a disk.")
                return
            self._show_confirm()
        elif self.step == 2:
            disk = self.selected_disk.get()
            if not messagebox.askyesno("Final Confirmation",
                f"⚠️  LAST WARNING\n\nAll data on {disk} will be PERMANENTLY erased.\n\nAre you absolutely sure?"):
                return
            self._show_install()

    def _back(self):
        if self.step == 1:
            self._show_welcome()
        elif self.step == 2:
            self._show_disk_select()

def main():
    # Must run as root
    if os.geteuid() != 0:
        # Re-launch with sudo
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    app = RIDOSInstaller()
    app.mainloop()

if __name__ == "__main__":
    main()
