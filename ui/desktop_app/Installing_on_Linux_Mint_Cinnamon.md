# 🚀 Installing VoiceMint on Linux Mint Cinnamon

This guide provides generalized instructions for setting up VoiceMint as a native desktop application on your specific system.

## 🛠️ Phase 1: Preparation

1.  **Identify your project's absolute path.** Open a terminal inside the project folder and run:
    ```bash
    pwd
    ```
    *Copy the output (e.g., `/home/username/Projects/VoiceMint`). This is your `PROJECT_PATH`.*

2.  **Prepare your `.desktop` file.** In this folder, you will find `voicemint.desktop.template`. Open it in a text editor and replace all instances of `/PATH/TO/PROJECT` with your actual `PROJECT_PATH`. Save it as `voicemint.desktop`.

---

## 🚀 Phase 2: Installation

### 1. Register VoiceMint in the Applications Menu
Copy your modified `.desktop` file to your local applications directory:

```bash
# Make the file executable
chmod +x voicemint.desktop

# Copy to the applications menu folder
cp voicemint.desktop ~/.local/share/applications/
```

### 2. Enable Autostart on Login (Optional)
If you want VoiceMint to launch automatically when you log in:

```bash
mkdir -p ~/.config/autostart
cp voicemint.desktop ~/.config/autostart/
```

---

## 🔐 Phase 3: Hardware Permissions (Required)

VoiceMint interacts with the Linux kernel's `uinput` for zero-latency typing. You must give your user permission to access this device without `sudo`:

1.  **Add your user to the input group:**
    ```bash
    sudo usermod -aG input $USER
    ```

2.  **Apply a udev rule:**
    ```bash
    echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
    ```

3.  **RESTART your computer.** This step is required for the permission changes to apply.

---

## 🛠️ Phase 4: Troubleshooting

- **Check Logs**: If the app fails to launch, view the log file at:
  `PROJECT_PATH/logs/voice_typing_logs.log`
- **Verify Virtual Environment**: Ensure your Python virtual environment is named `voicemint` and located in the project root.
- **Applying Updates**: If you ever move the project folder or change the icon, you must re-copy the `.desktop` file using the commands in Phase 2.
