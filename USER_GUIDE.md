# 📖 VoiceMint User Guide

Welcome to the comprehensive user manual for VoiceMint! This guide covers everything from basic usage and hotkeys to extending the application with your own custom LLM prompts and Speech-to-Text (STT) providers.

> **Note:** For installation instructions, please refer to the `README.md` and the `Installation_Deep_Dive.md` files.

---

## 1. 🔑 Setting Up Environment Keys

Before running the application, you must set up your API keys. VoiceMint relies on external cloud providers for Speech-to-Text and LLM formatting.

1.  Create a `.env` file in the root directory of the project.
2.  Add your API keys for the providers you intend to use. 

```env
SONIOX_API_KEY=your_soniox_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
GEMINI_API_KEY=your_gemini_key_here
```

*Note: You only need to provide keys for the specific STT and LLM services you actually plan to use. Deepgram is currently not enabled by default.*

---

## 2. 🎙️ General Usage

### 2.1 Starting the Application
How you launch VoiceMint depends on how you installed it:
*   **Desktop Application:** If you set up the desktop app (as explained in the Installation Deep Dive document), simply open the desktop app from your application menu.
*   **Terminal (Development Mode):** If you have not installed the desktop app and are just using this as a Python project, open your terminal, navigate to the project's root directory, and run:
    ```bash
    python main.py
    ```

### 2.2 Using Voice Typing
Once VoiceMint is running, you can control the voice dictation using two methods:
1.  **Floating UI:** Click the **Start** button on the application window to begin capturing audio from your default system microphone and streaming it to your chosen Speech-to-Text (STT) API. Click **Stop** to end the session.
2.  **Global Shortcuts:** Use your keyboard for seamless control. The default shortcut to start voice typing is `Super + U`. To stop, press `Super + I`.

**Injecting Text:**
After you start voice typing, simply click your cursor into any active text input box—this can be a web browser, a chat application, or even a terminal window. As you speak, your words will be instantly transcribed and injected directly into that text box.

### 2.3 Minimizing and Exiting
VoiceMint is designed to stay out of your way:
*   **Minimizing:** Clicking the "X" (close) button on the floating UI window **does not** quit the application. Instead, it minimizes the window to your taskbar (system tray). 
*   **Restoring:** You can bring the UI back at any time by right-clicking the VoiceMint icon in your taskbar and selecting "Open VoiceMint".
*   **Completely Exiting:** To fully shut down the application:
    *   If running as a desktop app, right-click the taskbar icon and select "Quit VoiceMint".
    *   If running from the terminal, you must manually stop the Python process (e.g., using `Ctrl + C`).

### 2.4 Taskbar Status Indicators
The native tray icon provides a quick visual cue of your current status and potential API billing:
*   **Green Icon:** Voice typing is **inactive**. The microphone is off, and you are not connected to the streaming STT API.
*   **Red Icon:** Voice typing is **active**. The microphone is capturing audio, and you are actively streaming data to the STT API (which signifies that you are being billed for this usage).

---

## 3. 🎛️ GUI Settings & Hotkeys

The VoiceMint GUI provides easy access to a variety of settings, allowing you to customize your experience without having to manually edit Python configuration files. You can open the settings panel by clicking the **"⚙ Settings"** button on the floating UI.

### 3.1 Application Settings
*   **Active STT Provider:** Choose which streaming speech-to-text provider to use. Currently, you can select between **Soniox** or **AssemblyAI**.
*   **Injection Method:** Choose between `Uinput` (which simulates actual hardware key presses) or `Clipboard` (which uses a smart copy-paste fallback). Try out both settings to see what feels better for your use case, but in general, `Clipboard` is recommended for most users.

### 3.2 Hotkeys
VoiceMint allows you to start and stop voice typing without clicking buttons by using default global hotkeys. 
*   **Start Listening:** `Super + U`
*   **Stop Listening:** `Super + I`
*   **Copy Last Message:** `Super + H`

**Feature Highlight: Copy Last Message**
If you ever dictate something and accidentally delete it, inject it in the wrong place, or if the injection didn't work (for example, in certain terminals), you can simply press `Super + H`. This will fetch the last transcribed session from memory and instantly paste it at your current cursor position.

If you want to change these shortcuts, you can do so directly within the "Hotkeys" tab in the GUI settings (or manually in the config file).

### 3.3 History
In the History tab, you can change how many of your previous voice messages are kept in memory and saved to disk. You can also directly view your last 3 voice messages using the built-in History Viewer.

### 3.4 Clipboard Injection
If you prefer using the Clipboard injection method, this tab helps you tune various aspects of how text is pasted. For example, if you prefer that longer sentences are inputted rather than short bursts of text, you can increase the **Ideal Flush Word Count**.

*Note: After clicking "Save & Exit", VoiceMint will perform a soft shutdown. You must manually relaunch the application for the new settings to take effect.*

---

## 4. ⚙️ Configuration Pipeline (`config.py`)

VoiceMint uses a multi-layered configuration system defined primarily in the `config.py` module. This file acts as the central single source of truth for the application's runtime environment.

*   **`config.json` (User Settings):** This auto-generated file stores user-editable preferences (like timeout durations, hotkeys, and active providers).
*   **`.env` (Secrets):** Server-side API keys (`SONIOX_API_KEY`, `ASSEMBLYAI_API_KEY`, `GEMINI_API_KEY`) are strictly loaded from your `.env` file using `python-dotenv`. They are never stored in the JSON config.
*   **`config.py` (Dynamic Loader):** On application startup, `config.py` reads the JSON file and the `.env` file. It parses strings into strict Python `Enum` classes (e.g., mapping the string `"soniox"` to `STTProvider.SONIOX`). This ensures the rest of the application runs with type-safe, validated settings.

---

## 5. 🌐 Chrome Extension Integration

The VoiceMint Chrome Extension provides an optional, but highly powerful add-on over the standard voice typing functionality. It acts as a bridge between your desktop dictation and your browser. Because the desktop app runs a local WebSocket server (port `6468`), the extension can communicate with it instantly. 

> **Note:** You do not need to use the Chrome extension to perform basic voice typing. This is purely for advanced text formatting and sending quick LLM requests. See the `Installation_Deep_Dive.md` file for installation instructions.

For the best experience, we suggest pinning the VoiceMint extension to your browser's toolbar.

### 5.1 The Extension Popup (`Ctrl + M`)
The primary way to interact with the extension is through its dedicated scratchpad popup.
1.  **Open the Popup:** Press `Ctrl + M` anywhere in your browser to instantly open the VoiceMint popup.
2.  **Input Text:** You can type text directly into the scratchpad box, paste text, or voice dictate directly into it.
3.  **Use Highlighted Text:** If you highlight text on a webpage and press `Ctrl + M`, that text will be automatically injected into the popup box. If no text is selected, the box will be empty.
4.  **Use Last Voice Message:** Click the "Use last voice message" button to instantly pull your most recent dictated message straight from the desktop app's history buffer into the popup.

### 5.2 Formatting with LLMs
The main purpose of the extension is to take your input text and send it to a Large Language Model (LLM) for processing or formatting—without having to open ChatGPT or Gemini in a new tab.

1.  **Choose a System Prompt:** Select a formatting instruction from the dropdown (e.g., "Clean up voice typing", "Fix grammar"). Because streaming Speech-to-Text APIs sometimes miss punctuation, make grammatical errors, or transcribe filler words like "um" and "ah", passing your raw dictation through an LLM is a great way to clean it up before sending.
2.  **Choose a Provider:** Select your preferred LLM provider.
3.  **Format:** Click "Format Text". VoiceMint will reach out to the LLM and output the formatted text below.

### 5.3 The Context Menu
For a faster workflow, you can bypass the popup entirely: highlight any text on a webpage, right-click, and select **"Add to VoiceMint"**. The extension will automatically format the text using your currently selected prompt and replace the text directly on the page.

---

## 6. 🧠 Extending the Functionality

VoiceMint is designed to be highly modular. You can easily add your own instructions, connect new AI models, or even swap out the core dictation engine.

### 6.1 Adding a New STT Provider
VoiceMint uses the Facade pattern to seamlessly swap out Speech-to-Text engines. To add a new real-time cloud STT provider:

1.  **Create the Handler:** Create a new Python file in `stt/stt_providers/` (e.g., `whisper_rt.py`).
2.  **Inherit from Base:** Create a class that inherits from `BaseTranscriber` (found in `stt/stt_providers/base.py`).
3.  **Implement the Methods:** You must implement three abstract methods:
    *   `start_connection(sample_rate)`: Establish the WebSocket connection.
    *   `send_audio_chunk(audio_chunk)`: Send raw PCM audio bytes to the server.
    *   `close_connection()`: Cleanly sever the connection.
4.  **Trigger the Callback:** Whenever your new STT engine receives text, call `self.callback(transcript_text, is_final_boolean)`.
5.  **Register the Provider:** Add your new provider to the `STTProvider` Enum in `config.py`, and update the factory function in `stt/stt_providers/manager.py` to instantiate it.

### 6.2 Adding a System Prompt
You can add custom prompts to handle specific use cases—such as translating text into another language, or changing the tone to be more professional or casual.

1.  Navigate to the `llm/prompts/` directory.
2.  You will find a template file called `system_prompt.py.template`. Copy this file and rename it (e.g., `03_formal_email.py`). *Make sure the new file ends in `.py`.*
3.  Edit the `SYSTEM_PROMPT` string variable inside your new file with whatever instructions you want.
4.  Restart the VoiceMint application. This new prompt will now automatically show up in the dropdown inside the Chrome extension.

### 6.3 Adding a New LLM Provider
1.  Add your provider's API key to your `.env` file.
2.  In `config.py`, add your provider to the `LLMProvider` Enum.
3.  Create a new file in `llm/providers/` (e.g., `openai_gpt.py`) with an `async def format_text(text: str, system_prompt: str) -> str:` function.
4.  Update `llm/manager.py` to import your new function and route traffic to it when your provider is selected.
5.  In the Chrome extension's `popup.js`, add a display name for your new provider in the `PROVIDER_DISPLAY_NAMES` dictionary. **(This step is compulsory, as it determines how the provider shows up in the Chrome extension dropdown).**

---

## 7. 🐛 Troubleshooting & Logs

If VoiceMint behaves unexpectedly, your first stop should always be the system logs.

*   **Log Location:** `logs/voice_typing_logs.log` (Relative to the project root).
*   **Log Rotation:** The app uses a `TimedRotatingFileHandler` that creates a new log file daily at midnight, keeping the last 7 days by default.
*   **Common Issues:**
    *   *Microphone not working / "Invalid sample rate":* Ensure you followed the setup guide for running without `sudo`. Running VoiceMint as root causes it to bypass user-level audio drivers (PulseAudio/PipeWire).
    *   *App won't start:* Check if a stale lock file exists at `/tmp/voicemint.lock`. VoiceMint enforces a single instance using this lock.
    *   *Extension says "Server Offline":* Ensure the VoiceMint desktop app is running, as it hosts the local WebSocket server required for the extension.
