# Linux Permissions & Audio Setup

This guide explains how to configure your Linux system (specifically Linux Mint/Cinnamon) to run VoiceMint as a standard user without `sudo` privileges.

## Why is this necessary?

By default, Linux restricts access to the virtual input device node (`/dev/uinput`) to the `root` user only. However, running this application with `sudo` creates a conflict with your audio system:

1.  **Audio Context**: Your microphone settings, PulseAudio, and PipeWire configurations are tied to your standard user session. When you run with `sudo`, the application runs as `root`, which uses raw ALSA hardware access. This often leads to "Invalid sample rate" errors or failure to detect your selected default microphone.
2.  **Security**: Running a background application as `root` is generally discouraged. 

By following the steps below, you grant your standard user the specific permissions needed to inject text via `evdev` while maintaining your user-level audio settings.

---

## Setup Instructions

> **Note:** These commands only need to be run **once** per system. Once configured, the permissions will persist across reboots and future updates.

Run these commands in your terminal once on any new Linux Mint/Cinnamon machine:

### 1. Create the `uinput` Group
This creates a dedicated system group for users allowed to access the virtual keyboard.
```bash
sudo groupadd -f uinput
```

### 2. Add Your User to the Group
Grant your current user account membership in the `uinput` group.
```bash
sudo usermod -aG uinput $USER
```

### 3. Create the udev Rule
This tells the Linux kernel to automatically grant the `uinput` group read/write access to the virtual keyboard hardware node.
```bash
echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules
```

### 4. Reload System Rules
Apply the changes immediately without rebooting (though a logout is still required).
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## ⚠️ Important Final Step

**You must log out and log back in (or restart your computer)** for the group membership changes to take effect. 

Once you have logged back in, you can verify your membership by running `groups`. If `uinput` is in the list, you can now run the application normally:

```bash
# Example execution (assuming you are in the project root)
./voicemint/bin/python main.py
```
