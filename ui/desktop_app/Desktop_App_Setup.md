# 🚀 VoiceMint: Linux Mint Desktop Setup Guide

Follow these instructions to integrate VoiceMint as a native application in your Linux Mint Cinnamon desktop environment.

## 1. Register VoiceMint in the Applications Menu

To make VoiceMint searchable in the Cinnamon "Start" menu, copy the provided `.desktop` file to your local applications folder:

```bash
# Ensure the file is executable
chmod +x /home/varun/Desktop/Projects/Python/VoiceMint/ui/desktop_app/voicemint.desktop

# Copy to the local applications directory
cp /home/varun/Desktop/Projects/Python/VoiceMint/ui/desktop_app/voicemint.desktop ~/.local/share/applications/
```

## 2. Enable Autostart on Login

If you want VoiceMint to start automatically whenever you log into Linux Mint:

```bash
# Copy the desktop file to the autostart directory
mkdir -p ~/.config/autostart
cp /home/varun/Desktop/Projects/Python/VoiceMint/ui/desktop_app/voicemint.desktop ~/.config/autostart/
```

## 3. Critical: Hardware Permissions (Uinput)

VoiceMint uses the Linux Kernel's `uinput` system for zero-latency typing. To ensure the desktop app can type without asking for a password, your user must be in the `input` group:

```bash
# Add your user to the input group
sudo usermod -aG input $USER

# Apply a udev rule to ensure uinput is always accessible to the input group
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules

# IMPORTANT: You MUST restart your computer for these permission changes to take effect.
```

## 4. Troubleshooting Desktop Launch

If the app fails to launch from the menu:
1. Check the logs: `tail -f /home/varun/Desktop/Projects/Python/VoiceMint/logs/voice_typing_logs.log`
2. Ensure the absolute paths in `voicemint.desktop` are correct.
3. Verify that the virtual environment is intact:
   ```bash
   ls /home/varun/Desktop/Projects/Python/VoiceMint/voicemint/bin/python3
   ```

## 5. Desktop Icon
The app will use the icon specified in the `.desktop` file. Currently set to:
`/home/varun/Desktop/Projects/Python/VoiceMint/assets/icon-on-128.png`

## 6. Applying Updates (Icon or Path Changes)
If you ever change the icon, name, or paths inside `voicemint.desktop`, you must re-sync the file for the changes to show up in your menu:

```bash
# Re-copy to applications menu
cp /home/varun/Desktop/Projects/Python/VoiceMint/ui/desktop_app/voicemint.desktop ~/.local/share/applications/

# Re-copy to autostart (if enabled)
cp /home/varun/Desktop/Projects/Python/VoiceMint/ui/desktop_app/voicemint.desktop ~/.config/autostart/
```
