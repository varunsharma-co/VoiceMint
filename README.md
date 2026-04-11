# 🎙️ Voice Mint Overview

Hi there! Welcome to VoiceMint. 

[Put a demo here]

I built this project because I wanted a truly native, lightweight, and highly accurate voice dictation tool for Linux Mint. While there are popular tools like WhisperFlow for macOS and Windows, the Linux ecosystem is often left behind. Furthermore, existing paid voice typing tools can cost upwards of $20 per month. 

VoiceMint is my personal take on solving this problem. By leveraging fast streaming cloud APIs instead of running heavy local Whisper models (which require powerful GPUs or sacrifice accuracy for size), VoiceMint brings highly accurate, real-time voice typing to your Linux desktop without bogging down your CPU. It captures your voice, processes it online, and injects the text straight into your cursor just as if you had typed it on a physical keyboard. 

The best part? It's incredibly affordable. Based on my usage, API costs are typically less than $1 per month (and AssemblyAI even offers $50 in free credits to new users!). I'm sharing this in hopes that it might be helpful to others in the Linux community looking for a seamless, budget-friendly dictation solution.

## ✨ Key Features

* **Extremely Lightweight & Minimal Resource Usage:** Designed to run on almost any PC, even 10-year-old systems. When idle, CPU usage is 0%. When actively dictating, it uses barely ~0.1% CPU and less than 100 MB of RAM. No expensive GPU is required! (RAM usage can be decreased even further by removing the LLM library if not needed).
* **Real-Time Universal Text Injection:** Injects text directly into your active OS cursor (in websites, browsers, notepads, terminals, etc.) as soon as the *final* transcript is received from the cloud API. It waits for natural pauses in your speech to deliver a fluid, real-time typing feel.
* **High Transcription Accuracy:** By using state-of-the-art online STT models (like Soniox and AssemblyAI), you get top-tier transcription accuracy without the errors common in small, locally-hosted offline models.
* **Auto-Silence Detection (Billing Protection):** Forgot to turn off the microphone? No problem. VoiceMint features a configurable silence timeout (default 45 seconds) that automatically severs the WebSocket connection when you stop speaking, preventing unexpected API billing shocks.
* **LLM Text Formatting (Chrome Extension):** Acts as a force multiplier for your dictation. Make a secondary API call via the companion Chrome Extension to apply custom system prompts. Instantly translate text, fix grammar, or rewrite your spoken words into a formal or casual tone.
* **Instant Connection:** The moment you open the app, it instantly connects to the streaming speech-to-text provider, ensuring a seamless and immediate start to your dictation workflow.
* **Native Linux Mint Integration:** Fills a major gap in the Linux dictation space. It integrates perfectly with Linux Mint's environment, utilizing robust default libraries and global hotkeys.
* **Highly Customizable:** Tailor the application to your exact workflow. Easily change global keyboard shortcuts, timeout durations, and injection methods directly from the built-in GUI settings.

## 🏗️ Architecture Overview

VoiceMint was engineered from the ground up to be as lightweight and unobtrusive as possible. Here is a look at the technical decisions that make it work:

* **I/O-Bound Threading over Multiprocessing:** Because the app spends most of its time waiting on microphone input and WebSocket network responses, it is highly I/O-bound. I opted for Python's native `threading` module rather than heavy `multiprocessing`. This effectively bypasses the Global Interpreter Lock (GIL) during wait times while consuming only a fraction of the system RAM.
* **Thread Isolation & Concurrency:** To ensure the app remains perfectly responsive, critical processes are isolated. The `tkinter` UI safely owns the main thread (a strict requirement for X11 stability). Meanwhile, the GTK System Tray, the WebSocket server, the global hotkey listener, and the text-injection consumer all run independently on dedicated background threads, ensuring no single task blocks the system.
* **Lightweight GUI (`tkinter`):** I specifically chose `tkinter` for the settings and status UI. While it might look slightly old-school, it requires practically zero overhead, keeping idle CPU usage at 0% and RAM usage incredibly low.
* **Resource-Efficient Silence Timeout:** Instead of running a computationally expensive localized Voice Activity Detection (VAD) model to know when you stop speaking, VoiceMint uses a lightweight timer. If the active STT provider returns no text for a configurable duration, the app automatically severs the WebSocket connection. This prevents infinite API billing without taxing your CPU.
* **Dual Text-Injection Engines:**
  * **Primary (`uinput`):** Uses the `evdev` module to act as a literal virtual hardware keyboard, injecting scancodes at the OS kernel level for true zero-latency typing.
  * **Fallback (Clipboard):** For complex language character sets, the app falls back to a highly secure clipboard injection method. It backs up your current clipboard, pastes the API text using `Shift+Insert`, and instantly restores your original clipboard data, leaving your workflow untouched.
* **Minimalist Dependencies:** To maintain the low-footprint ethos, I avoided heavy frameworks. Global keyboard shortcuts are handled natively via `pynput` (instead of messy bash scripts). The bridge between the Python backend and the Chrome Extension uses lightweight, native `websockets` rather than spinning up a bloated `FastAPI` server.
* **Extensible Design (Facade & DRY Principles):** The core logic is hidden behind Abstract Base Classes (`BaseInjector`, `BaseTranscriber`). This makes the architecture highly extensible—adding a new STT provider or a future text injection method is as simple as writing a new subclass, strictly adhering to DRY (Don't Repeat Yourself) principles.
* **Safe Teardown via Context Managers:** The creation of the `uinput` virtual keyboard and the management of audio streams utilize context managers and graceful thread events. Whether you toggle the mic on/off fifty times a day or close the app entirely, this guarantees that all virtual hardware is released and sockets are closed cleanly, preventing any system resource leakage.

## 🚀 Quick Start

Below are the quick commands to get VoiceMint up and running on your machine. If you'd like a detailed explanation of exactly what these commands are doing under the hood, please refer to the [Installation Deep Dive](Installation_Deep_Dive.md) guide.

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

* **Native Desktop App:** For instructions on setting up the VoiceMint desktop icon and enabling auto-start on login, check out [Section 3 of the Installation Deep Dive](Installation_Deep_Dive.md#step-3---setup-of-the-desktop-file-and-icon-optional).
* **Chrome Extension:** To install the companion browser extension for LLM formatting, follow [Section 4 of the Installation Deep Dive](Installation_Deep_Dive.md#step-4---chrome-extension-setup-optional).

## 💡 Usage

To help you get the absolute most out of VoiceMint, I've put together a dedicated guide. Please head over to the [User Guide](USER_GUIDE.md) for comprehensive details on default hotkeys, managing settings, using the session history, and making the most of the Chrome extension. 

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT) - see the LICENSE file for details. You are completely free to use, modify, and distribute this software however you see fit!
