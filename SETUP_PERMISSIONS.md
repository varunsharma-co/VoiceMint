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

---
***

### Setting Up the Native Linux System Tray (VoiceMint)

To run the native GTK system tray icon and notifications on Linux Mint Cinnamon, you need to install the underlying system C-libraries and compile the Python bindings. 

*Note* that these sudo install commands need to be run before we install PyGObject library using pip within our virtual envoirnment.

#### 1. Install System Dependencies
Before installing the Python packages, your operating system needs the modern `AyatanaAppIndicator` library to render the tray icon, as well as the C-compilers to build the Python bridge.

Run the following command in your terminal (outside or inside your virtual environment, it does not matter):

```bash
sudo apt-get update
sudo apt-get install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

* **What this does:** * `gir1.2-ayatanaappindicator3-0.1`: The modern, system-level Linux tray renderer.
  * `gir1.2-gtk-3.0`: The core GTK UI framework.
  * `libgirepository1.0-dev`, `gcc`, `pkg-config`, etc.: The C-compilers and headers required for `pip` to successfully build the Python wrapper.

#### 2. Install Python Dependencies
Once the system libraries are installed, you need to install `PyGObject` inside your isolated virtual environment. This acts as the bridge between Python and the native Linux GTK libraries.

**First, ensure your virtual environment is activated:**
```bash
source venv/bin/activate  # Or whichever activation command you use
```

**Then, install the package:**
```bash
pip install PyGObject
```

#### 3. Audio Playback Note
There are no additional Python libraries (like `pygame` or `pydub`) required for notification sounds. VoiceMint uses the `aplay` command-line tool, which comes pre-installed natively on Linux Mint.
