# Linux Voice-Typing Task Template

## 1. Task Overview

### Task Title
**Title:** Implement CustomTkinter GUI and Pynput Global Hotkeys

### Goal Statement
**Goal:** Build a basic graphical user interface using CustomTkinter that manages the application state (Start/Stop listening), and implement global hotkey listeners using `pynput` (Super+U and Super+I) that suppress the native key presses while triggering the STT pipeline. The main application will initialize the virtual keyboard context manager upon startup and keep it alive while the GUI runs.

---

## 3. Strategic Analysis & Solution Options

### Problem Context
The application needs a user interface to display its current state and manual controls for starting/stopping the voice typing session. Furthermore, the global hotkey mechanism requires a transition from `keyboard` to `pynput` to avoid root access issues on Linux, whilst ensuring that the trigger keys (Super+U, Super+I) are suppressed and not accidentally typed into the active window. The virtual keyboard (`evdev.UInput`) context manager must be initialized when the app starts and closed when the app exits.

### Solution Options Analysis

#### Option 1: Pynput Listener with `suppress=True`
**Approach:** Create a dedicated background thread running `pynput.keyboard.GlobalHotKeys` or a custom `pynput.keyboard.Listener(..., suppress=True)` to intercept `Super+U` and `Super+I`. The main thread runs the CustomTkinter `mainloop()`. The application initializes `evdev.UInput` before starting the GUI.
**Pros:**
- ✅ Native Python support for event suppression.
- ✅ Does not require root access like the `keyboard` module.
**Cons:**
- ❌ `pynput` suppression can sometimes be tricky on specific Linux/X11 or Wayland setups.

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option 1 - Pynput Listener with `suppress=True`. This directly addresses the root access problem and fulfills the suppression requirement outlined by the user.

### Decision Request
**👤 USER DECISION REQUIRED:**
Based on this analysis, do you want to proceed with the recommended solution (Option 1), or would you prefer a different approach?

---

## 4. Context & Problem Definition

### Problem Statement
Currently, `main.py` is a terminal script that blocks on `start_listening()`. It needs a graphical interface and global hotkeys to be usable as a background desktop utility. The previous instruction to use the `keyboard` library causes permission issues on Linux.

### Success Criteria
- [ ] A CustomTkinter window appears on startup with Start/Stop buttons, a status indicator (color square), and an "Always on Top" checkbox.
- [ ] `config.py` contains `HOTKEY_START` and `HOTKEY_STOP` variables.
- [ ] Global hotkeys (Super+U and Super+I) start and stop the STT pipeline respectively, using `pynput`.
- [ ] The actual key characters (u/i) are suppressed and not typed into the user's active window.
- [ ] The `evdev.UInput` context manager is initialized on app startup and released on exit.

---

## 6. Technical Requirements

### Functional Requirements
- GUI must display the current listening state (e.g., Red square for Stopped, Green for Listening).
- Checkbox to toggle "Always on Top" property for the window.
- Hotkeys toggle the `utils.is_listening` event and start/stop the mic and WebSocket streams.

### Non-Functional Requirements
- **Thread Safety:** The UI must run on the Main Thread (`mainloop()`). `pynput` listener runs on a background thread. Voice pipeline updates to the UI must use `.after()` or thread-safe variable tracing.

### Technical Constraints
- Must use `customtkinter` for the GUI.
- Must use `pynput` for hotkeys.

---

## 8. STT Providers & WebSockets

### WebSocket Lifecycle
- [ ] When the Start hotkey/button is triggered, the mic and WebSocket should connect.
- [ ] When the Stop hotkey/button is triggered, the mic and WebSocket should disconnect gracefully.

---

## 10. Code Quality Standards & Best Practices

### Python Code Quality Requirements
- [ ] **Thread-Safe UI Rule:** Explicitly forbid updating CustomTkinter widgets from background threads. Use `.after()`.
- [ ] **Context Manager Rule:** `evdev.UInput` must be initialized at application startup and properly closed on exit.
- [ ] **🚨 USE PIP:** Always use `pip` and `requirements.txt` for dependency management.

---

## 11. Implementation Plan

### Phase 1: Configuration & Dependencies
**Goal:** Add necessary config variables and install `customtkinter` and `pynput`.
- [x] **Task 1.1:** Add `HOTKEY_START = '<super>+u'` and `HOTKEY_STOP = '<super>+i'` to `config.py`. (✓ 2026-04-07 17:44)
- [x] **Task 1.2:** Update `requirements.txt` with `customtkinter` and `pynput`. (✓ 2026-04-07 17:44)

### Phase 2: Hotkey Listener Implementation
**Goal:** Implement the `pynput` listener logic to suppress and handle the hotkeys.
- [x] **Task 2.1:** Create `utils.py` listener or a dedicated hotkey manager to run the `pynput` listener thread. (✓ 2026-04-07 17:44)

### Phase 3: GUI Implementation
**Goal:** Build the CustomTkinter GUI in `ui/floating.py` and expose it via `ui/__init__.py`.
- [x] **Task 3.1:** Implement the application UI class in `ui/floating.py` using `customtkinter.CTk`. (✓ 2026-04-07 17:44)
- [x] **Task 3.2:** Add Start/Stop buttons, status indicator, and Always on Top checkbox. (✓ 2026-04-07 17:44)
- [x] **Task 3.3:** Export the UI class/launcher in `ui/__init__.py` to follow the Facade Pattern. (✓ 2026-04-07 17:44)

### Phase 4: Hotkey & Orchestration Refactoring
**Goal:** Implement hotkey logic in a separate module and refactor `main.py` for pure orchestration.
- [x] **Task 4.1:** Create `ui/hotkeys.py` to handle the `pynput` listener logic and suppress keys. (✓ 2026-04-07 17:44)
- [x] **Task 4.2:** Update `main.py` to only handle high-level orchestration (initializing hardware, starting threads/GUI) and avoid internal business logic. (✓ 2026-04-07 17:44)

### Phase 5: Basic Code Validation (AI-Only)
- [x] **Task 5.1:** Code Quality Verification (✓ 2026-04-07 17:44)
- [x] **Task 5.2:** Import and Syntax Validation (✓ 2026-04-07 17:44)

### Phase 6: Manual Code Review (Mandatory)
- [ ] **Task 6.1:** Present Implementation Complete Message (MANDATORY)
- [ ] **Task 6.2:** Final Manual Verification (By User)

---

## 15. Deployment & Configuration

### Environment Variables
No new environment variables needed for this task. `config.py` handles the new constants.
