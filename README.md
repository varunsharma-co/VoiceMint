# 🎙️ Voice Mint (WisprFlow Alternative)

I built this app because I wanted a truly native, lightweight, and highly accurate voice dictation tool for Linux Mint. 

There are popular tools like WhisperFlow, but not for Linux. Plus they cost like $20 per month. 

VoiceMint solves this problem... 

➡️ VM leverages fast streaming STT APIs for highly accurate voice typing instead of running heavy local Whisper models (which require powerful GPUs or sacrifice accuracy for size)

➡️ The best part? 

It's incredibly affordable. 

Based on my usage, API costs are around **$1** per month (and AssemblyAI even offers $50 in free credits to new users!). 

I'm sharing this in hopes that it might be helpful to others in the Linux community looking for a seamless, budget-friendly voice-typing solution.

Here's a quick demo:

[Click Here to View A Demo + Advanced Usage Example](https://www.youtube.com/watch?v=26dcf9Uwptk)


## ✨ Key Features

* **Extremely Lightweight & Minimal Resource Usage:** Can run on even 10-year-old PCs. 0% CPU usage when idle, ~0.1% active.


* **Real-Time Universal Text Injection:** Injects text directly into your active OS cursor (in websites, browsers, notepads, terminals, etc.).

* **High Transcription Accuracy:** Uses the best STT models (like Soniox and AssemblyAI).

* **Auto-Silence Detection (Billing Protection):** Auto silence detection to turn off the mic when not in use.

* **LLM Text Formatting (Chrome Extension):** Can apply custom formatting to voice-typed text. Like fix grammar, or rewrite your spoken words into a formal or casual tone. Or translate text to another language.

* **Almost Instant Connection:** You press the keyboard shortcut and start voice typing almost immediately.


* **Highly Customizable:** Tailor the application to your exact workflow. Easily change global keyboard shortcuts, timeout durations, and injection methods directly from the built-in GUI settings.

## 🏗️ Architecture Overview

A quick look at the technical decisions I took to keep VoiceMint as lightweight and unobtrusive as possible:

* **Minimalist Dependencies:** Avoids bloated frameworks. Global hotkeys run via native pynput. The Chrome Extension bridge uses lightweight websockets rather than a heavy FastAPI server.

* **I/O-Bound Threading:** Instead of heavy `multiprocessing`, VoiceMint uses Python's native `threading`. This bypasses the Global Interpreter Lock (GIL) during I/O wait times and consumes only a fraction of system RAM.

* **Zero-Overhead GUI:** Built specifically with `tkinter`. It might look old-school, but it requires practically zero overhead, keeping idle CPU at 0% and RAM usage incredibly low.

* **Smart Silence Timeout:** Instead of a computationally expensive Voice Activity Detection (VAD) model, VoiceMint uses a lightweight timer. If no text is returned for a set duration, the connection closes automatically.

* **Thread Isolation:** To keep the app perfectly responsive, critical processes are isolated. The `tkinter` UI safely owns the main thread, while background tasks (System Tray, WebSocket server, hotkey listener, text injection) run independently.

* **Dual Text-Injection Engines:**
  * **Primary (`uinput`):** Acts as a literal virtual hardware keyboard, injecting scancodes at the OS kernel level for zero-latency typing.
  * **Fallback (Clipboard):** For complex character sets, it backs up your clipboard, pastes the API text via `Shift+Insert`, and instantly restores your original clipboard data.
  

* **Extensible Design:** Core logic is hidden behind Abstract Base Classes. Adding a new STT provider or injection method is as simple as writing a new subclass, strictly following DRY principles.

* **Safe Teardown:** Context managers guarantee all virtual hardware is released and sockets are closed cleanly on shutdown, preventing any system resource leakage.


## 🚀 Quick Start

Below are the quick commands to get VoiceMint up and running on your machine. 

If you'd like a detailed explanation of exactly what these commands are doing under the hood, please refer to the [Installation Deep Dive](Installation_Deep_Dive.md) guide.

### 1. System Permissions & Dependencies

VoiceMint requires specific permissions to inject text directly via the Linux kernel, as well as some system libraries to render the native GTK tray icon. Run all of these `sudo` commands at once in your terminal:

```bash
# Create the uinput group and add your user to it
sudo groupadd -f uinput
sudo usermod -aG uinput $USER

# Apply the udev rule for hardware access
echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules

# Reload system rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Install GTK tray and Tkinter system dependencies
sudo apt-get update
sudo apt-get install -y libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 python3-tk
```

**⚠️ Important:** You *must* log out and log back in (or restart your computer) right now for the group permission changes to take effect!


### 2. Install Python Requirements

Once you have rebooted, navigate into the root directory of the project, activate your virtual environment, and install the required Python packages:

```bash
pip install -r requirements.txt
```


### 3. Setup API Keys (.env)

VoiceMint uses external APIs for speech-to-text and AI text formatting. Before running the app, you need to configure your API keys.

Copy the provided example environment file:
```bash
cp .env.example .env
```
Then, open the newly created `.env` file and insert your keys for the following services:
* **Soniox API Key** (Primary STT)
* **AssemblyAI API Key** (Alternative STT)
* **Gemini API Key** (LLM provider for the Chrome Extension)


### 4. Desktop App & Extension Setup

To make this feel like a true native app, you'll want to add it to your Linux Mint application menu and set up the browser extension.

* **Native Desktop App:** To set up the desktop icon and enable auto-start, check out [Section 3 of the Installation Deep Dive](Installation_Deep_Dive.md#step-3---setup-of-the-desktop-file-and-icon-optional).
* **Chrome Extension:** To install the companion browser extension for LLM formatting, follow [Section 4 of the Installation Deep Dive](Installation_Deep_Dive.md#step-4---chrome-extension-setup-optional).


## 💡 Usage

To help you get the absolute most out of VoiceMint, I've put together a dedicated guide. Please head over to the [User Guide](USER_GUIDE.md) for comprehensive details on default hotkeys, managing settings, using the session history, and making the most of the Chrome extension. 


## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT) - see the LICENSE file for details. You are completely free to use, modify, and distribute this software however you see fit!
