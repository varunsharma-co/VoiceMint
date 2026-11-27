# Installation Deep Dive

> **Note:** For quick, copy-paste installation instructions, please refer to the `README.md` file. This guide provides a detailed breakdown and explanation of what each of those commands does for users who want to understand the underlying setup process.

Before running the application, we need to set up the environment. It is crucial that these commands are run in order: 
- system-level commands (`sudo`) must be executed first, 
- followed by the Python package installation (`pip`). 

The remaining steps (Desktop App and Chrome Extension) are optional but highly recommended for a complete experience.

## Step 1 - System-Level Setup & Permissions (`sudo`)

This section explains how to install required system libraries and configure your Linux system (specifically Linux Mint/Cinnamon) to grant VoiceMint the necessary permissions.

### 1.1 Installing System Dependencies (UI & Tray)

VoiceMint relies on native system UI components for its floating window and system tray. We need to install the underlying C-libraries and the `tkinter` framework via the system package manager (`apt`).

**Run the following commands in your terminal:**

1. **Update package lists:**
   ```bash
   sudo apt-get update
   ```

2. **Install Tray and Compilation Dependencies:**
   ```bash
   sudo apt-get install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
   ```
   * **Why?** This installs the modern `AyatanaAppIndicator` library (for the tray icon), the GTK3 UI framework, and the C-compilers needed for `pip` to successfully build the Python bridge (`PyGObject`) later.

3. **Install Tkinter:**
   ```bash
   sudo apt-get install python3-tk
   ```
   * **Why?** `tkinter` is a system-level library responsible for rendering the main floating UI. It must be installed globally rather than through Python's `pip`. Once installed, your virtual environment will automatically have access to it.

---

### 1.2 Configuring `evdev` Permissions

By default, Linux restricts access to the virtual input device node (`/dev/uinput`) to the `root` user only. However, running VoiceMint with `sudo` creates a conflict with your audio system (PulseAudio/PipeWire), often leading to microphone detection failures or "Invalid sample rate" errors. 

To solve this, we grant your standard user the specific permissions needed to inject text seamlessly, without needing to run the app as root.

**Run these commands in your terminal (only required once per system):**

1. **Create the `uinput` Group:** Creates a dedicated system group for users allowed to access the virtual keyboard.
   ```bash
   sudo groupadd -f uinput
   ```

2. **Add Your User to the Group:** Grants your current user account membership in this new group.
   ```bash
   sudo usermod -aG uinput $USER
   ```

3. **Create the udev Rule:** Tells the Linux kernel to automatically grant the `uinput` group read/write access to the virtual keyboard hardware node.
   ```bash
   echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules
   ```

4. **Reload System Rules:** Applies the changes immediately without rebooting (though a logout is still required).
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

> ⚠️ **Important:** You **must log out and log back in** (or restart your computer) for the group membership changes to take effect.

***

## Step 2 - Python Dependencies (`pip`)

Once the system-level setup is complete, you need to install the specific Python packages required by VoiceMint.

Ensure your virtual environment (`voicemint`) is activated, then run the following command from the project root:

```bash
pip install -r requirements.txt
```

**What this does:** This installs all necessary libraries isolated within your environment, including `PyGObject` (using the C-libraries we installed earlier), `sounddevice` for audio capture, and `pynput` for global hotkeys.

🎉 **At this point, the core installation is complete!** You can launch VoiceMint by running `python main.py` in your terminal from the project root.

***

## Step 3 - Desktop App & Icon Integration (OPTIONAL)

These steps integrate VoiceMint into your native system environment, allowing you to launch it from the application menu, pin it to your panel, and configure it to start automatically on login.

### 3.1 Preparation

1. **Identify your project path:** Open a terminal in the root project folder and run:
   ```bash
   pwd
   ```
   *Copy the output (e.g., `/home/username/Projects/VoiceMint`). This is your `PROJECT_PATH`.*

2. **Prepare the desktop file:** Open the template located at `ui/desktop_app/voicemint.desktop.template` in a text editor. Replace all instances of `/PATH/TO/PROJECT` with your actual `PROJECT_PATH`. Save the new file as `ui/desktop_app/voicemint.desktop`.

### 3.2 Installation

Run these commands from the **root** project folder:

1. **Register VoiceMint in the Applications Menu:**
   ```bash
   chmod +x ui/desktop_app/voicemint.desktop
   cp ui/desktop_app/voicemint.desktop ~/.local/share/applications/
   ```

2. **Enable Autostart on Login (Optional):**
   ```bash
   mkdir -p ~/.config/autostart
   cp ui/desktop_app/voicemint.desktop ~/.config/autostart/
   ```

### 3.3 Troubleshooting Updates
* **Check Logs:** If the app fails to launch from the menu, check `PROJECT_PATH/logs/voice_typing_logs.log`.
* **Path Changes:** If you ever move the project folder, you must update the path in your `.desktop` file and re-copy it using the commands in Phase 2.

***

## Step 4 - Chrome Extension Setup (OPTIONAL)

The VoiceMint Chrome extension provides a floating scratchpad and LLM-powered text formatting directly within your browser, integrating seamlessly with the desktop app's WebSocket server.

### 4.1 Enable Developer Mode in Chrome
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. In the top right corner, toggle the **Developer mode** switch to **ON**.

### 4.2 Load the Extension
1. Click the **Load unpacked** button in the top left.
2. In the file picker, navigate to the root folder of your VoiceMint project.
3. Select the `chrome_extension` folder and click **Open**.

### 4.3 Usage & Features
* **Popup Scratchpad:** Click the VoiceMint icon in your browser (or press `Ctrl+M`) to open the notepad for formatting text.
* **Use Last Voice Message:** Click this button in the popup to instantly pull your most recent transcript from the desktop app into the browser.
* **Context Menu:** Highlight any text on a webpage, right-click, and select **Send to VoiceMint** to automatically format and replace it.

> **Note:** The desktop application must be running for the extension to retrieve voice messages or format text, as it relies on the local WebSocket server.
