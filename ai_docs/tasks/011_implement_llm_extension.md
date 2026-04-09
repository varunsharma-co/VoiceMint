# 011: Implement LLM Chrome Extension and WebSocket Server

## 1. Task Overview

### Task Title
**Title:** Implement LLM Chrome Extension & Python WebSocket Bridge

### Goal Statement
**Goal:** Expand the VoiceMint ecosystem by building a Chrome Extension that acts as a frontend for LLM-powered text formatting. Connect this extension to the native Python application via a persistent WebSocket server on port 6468.

---

## 2. Existing Codebase Analysis

### Existing Services & Modules Analysis
- **STT/Mic Flow:** Currently handles audio capture and streams to WebSocket providers, placing text in `transcript_queue`.
- **Injection Flow:** Reads from `transcript_queue` and uses `evdev` or clipboard.
- **LLM/Prompts:** Contains `01_voice_typing.py` and `02_pep_fan.py`.
- **LLM/Providers:** Contains `gemini_flash_2_5_lite.py`, which is currently a standalone script.
- **History:** `history.py` provides `get_recent_history()`.

### Current Workflow Understanding
- Voice typing is independent and handled by `ui` and `stt` packages.
- The new LLM server will operate as a standalone background `asyncio` WebSocket server running on the Python backend. It should be non-blocking to the existing `tkinter` and `pystray` main threads.

### Integration Decision Matrix
- **Create New Module:** The WebSocket server needs a dedicated asynchronous event loop since Tkinter and GTK run on their own threads. We will add an `llm/websocket_server.py` module to host the server and `llm/manager.py` to route API requests.

---

## 3. Strategic Analysis & Solution Options

### Problem Context
We need to run a persistent `websockets` asyncio server in a purely threaded Python application.

### Solution Options Analysis
#### Option 1: Asyncio Thread (Recommended)
**Approach:** Run the WebSocket server `serve()` loop inside a dedicated daemon `threading.Thread` using `asyncio.run()`.
**Pros:**
- ✅ Native Python `asyncio` compatibility without blocking `tkinter`.
- ✅ Complete isolation from core voice typing performance.
**Cons:**
- ❌ Minor thread overhead.

#### Option 2: Polling (Not Recommended)
**Approach:** Continuously poll a local HTTP server instead of WebSockets.
**Pros:** Simpler connection lifecycle.
**Cons:** Loss of bidirectional state, poor performance.

### Decision Request
**RECOMMENDED SOLUTION:** Option 1 - Asyncio Thread.

---

## 4. Context & Problem Definition

### Problem Statement
VoiceMint needs to process captured text and format it using local/remote LLMs directly from the browser. The user requested a Manifest V3 Chrome Extension connected to VoiceMint.

### Success Criteria
- [ ] Chrome extension installs cleanly and reacts to `Ctrl+Y`.
- [ ] Context Menu item "Send to VoiceMint" works.
- [ ] Python backend successfully boots `ws://localhost:6468` and handles `init` and `format` commands.
- [ ] LLM Manager routes requests dynamically based on the dropdown selections.
- [ ] History loads seamlessly into the extension on init.

---

## 5. Development Mode Context

- **🚨 IMPORTANT: This is a new application in active development**
- **Priority:** Minimal latency. The websocket server must be lightweight.

---

## 6. Technical Requirements

### Functional Requirements
- **Server:** Listen on `ws://localhost:6468`.
- **Actions:** `{ "action": "init" }` -> Returns `prompts`, `default_provider`, `recent_message`.
- **Actions:** `{ "action": "format", "text": "...", "prompt": "...", "provider": "..." }` -> Returns `{ "formatted_text": "..." }`.
- **Extension UI:** Dark/Light mode, two textareas, copy icons, dynamic dropdowns, "last message" inject button.
- **Hotkeys:** `Ctrl+Y` to open popup natively and inject selected text.

---

## 7. State & Persistence

### Chrome Extension State
- Use `chrome.storage.local` to persist the Dark/Light mode preference.

---

## 8. STT Providers & WebSockets

- We will use the `websockets` library for Python.
- The browser will maintain a persistent or on-demand `WebSocket` connection.

---

## 9. Code Organization & File Structure

### New Files to Create

```
VoiceMint/
├── llm/
│   ├── manager.py                   # Maps strings to providers/prompts
│   ├── websocket_server.py          # The asyncio WebSocket host
│   └── __init__.py                  # Exposes start_llm_server()
│
└── Voice-Typing-Extension/          # (New Extension Root)
    ├── manifest.json
    ├── background.js
    ├── popup.html
    ├── popup.css
    ├── popup.js
    └── icons/
        ├── copy-icon.svg
        └── icon-128.png
```

### Files to Modify
- `main.py` - Spawn the new `start_llm_server()` in a background thread.
- `llm/providers/gemini_flash_2_5_lite.py` - Remove the standalone execution block, convert to a clean callable function `async def format_text(...)`.
- `config.json` / `config.py` - Add `DEFAULT_LLM_PROVIDER` setting.

---

## 10. Code Quality Standards & Best Practices

- [ ] Complete type annotations.
- [ ] No blocking of the UI thread.
- [ ] Graceful termination on app exit (`utils.app_running.clear()`).

---

## 11. Implementation Plan

### Phase 1: Python LLM Backend Refactor
**Goal:** Setup the LLM module to handle structured requests.
- [ ] **Task 1.1:** Update `config.py` and `config.json` with `DEFAULT_LLM_PROVIDER`.
- [ ] **Task 1.2:** Modify `llm/providers/gemini_flash_2_5_lite.py` to be a stateless async function.
- [ ] **Task 1.3:** Create `llm/manager.py` to load prompts from files and route generation requests.

### Phase 2: Python WebSocket Server
**Goal:** Establish the `ws://localhost:6468` server.
- [ ] **Task 2.1:** Create `llm/websocket_server.py` using the `websockets` library.
- [ ] **Task 2.2:** Expose `start_llm_server()` and `stop_llm_server()` in `llm/__init__.py`.
- [ ] **Task 2.3:** Update `main.py` to start and safely stop the LLM server alongside the consumer thread.

### Phase 3: Chrome Extension Skeleton & UI
**Goal:** Build the Manifest V3 structural files and UI.
- [ ] **Task 3.1:** Create `manifest.json`, `background.js`, `popup.html`, and `popup.css`.
- [ ] **Task 3.2:** Implement Dark/Light mode toggle styling.

### Phase 4: Chrome Extension Logic
**Goal:** Implement the logic in `popup.js` and `background.js`.
- [ ] **Task 4.1:** Connect `popup.js` to `ws://localhost:6468`.
- [ ] **Task 4.2:** Implement the `init` action (load prompts, providers, fetch last message).
- [ ] **Task 4.3:** Implement `format` action (send text, receive and display formatted response).
- [ ] **Task 4.4:** Add Context Menu and Keyboard Shortcut logic to `background.js` and script injection logic.
