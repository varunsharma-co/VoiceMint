# Linux Voice-Typing Task Template

## 1. Task Overview

**Title:** Implement Threaded Chunked Buffer Clipboard Injection

**Goal:** Create a robust clipboard-based text injection engine that buffers incoming transcripts and executes bulk pastes using a strict three-tier trigger system and a ghost-paste prevention sequence. This handles languages with non-standard punctuation (e.g., Hindi) more reliably than sequential key presses.

---

## 3. Strategic Analysis & Solution Options

### Problem Context
The user requested a clipboard-based text injection method that batches text into a buffer and fires bulk pastes. This requires precise execution to avoid clipboard race conditions ("ghost pastes") where the OS pastes old clipboard data because the target app didn't register the new clipboard state quickly enough. 

**User's Question:** *"...im not sure if we'll need to use UInput to emulate pressing Shift + Insert to paste the text into selected text box. or if its a must have."*

**Analysis:** Yes, emulating the paste keystroke is a **must-have**. Setting the system clipboard programmatically (e.g., via `pyperclip` or `xclip`) only modifies the clipboard in memory; it does *not* force the active application (where your cursor is) to actually paste the text. You must simulate the user pressing a paste shortcut.

### Solution Options Analysis: Simulating the Paste Keystroke

#### Option 1: Reuse Existing `evdev` Engine (Recommended)
**Approach:** Use the existing `evdev` virtual keyboard to send a literal `Shift` + `Insert` hardware scancode.
**Pros:**
- ✅ Zero new external dependencies for keystroke simulation.
- ✅ Operates at the kernel level (perfect Wayland and X11 compatibility).
- ✅ We already solved the `udev` permission requirements in Task 002.
**Cons:**
- ❌ None, since the setup is already complete.

#### Option 2: Use `pynput`, `pyautogui`, or `keyboard`
**Approach:** Install a high-level library to simulate the hotkey.
**Pros:**
- ✅ Simpler API syntax.
**Cons:**
- ❌ Introduces heavy dependencies.
- ❌ Frequently breaks under modern Wayland compositors (which Linux Mint/Ubuntu are moving towards).

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option 1 - We will use a lightweight clipboard manager (like `pyperclip` or direct `xclip` subprocesses) to handle the text backup/loading, but we will strictly use our existing `evdev` setup to fire the `Shift + Insert` keystroke.

---

## 4. Context & Problem Definition

### Problem Statement
We need to implement a new `ClipboardInjector` that adheres to the `BaseInjector` interface but alters the behavior from "immediate typing" to "buffered batch pasting."

### Success Criteria
- [ ] Central tuning variables (`IDEAL_FLUSH_WORD_COUNT`, `FAILSAFE_FLUSH_MULTIPLIER`, `CLIPBOARD_RESTORE_DELAY_SEC`) added to `config.py`.
- [ ] `config.py` correctly defines `ACTIVE_INJECTION_METHOD` to easily switch between `UINPUT` and `CLIPBOARD` methods.
- [ ] Three-Tier Trigger system (Ideal, Failsafe, Cleanup) implemented successfully.
- [ ] Ghost Paste Prevention Sequence implemented with exact sleep timings.
- [ ] System clipboard is cleanly restored to its original state after a successful paste.

---

## 6. Technical Requirements

### Functional Requirements
- **Trigger 1 (Ideal Flush):** Buffer word count `>= IDEAL_FLUSH_WORD_COUNT` AND latest text ends with terminal punctuation (`.`, `?`, `!`).
- **Trigger 2 (Failsafe Flush):** Buffer word count `>= (IDEAL_FLUSH_WORD_COUNT * FAILSAFE_FLUSH_MULTIPLIER)`.
- **Trigger 3 (Cleanup Flush):** Triggered when the silence timeout is reached OR the user manually stops listening.
- **Ghost Paste Sequence:**
  1. **Backup:** Save current clipboard.
  2. **Load:** Set OS clipboard to buffer text.
  3. **Wait:** `time.sleep(0.05)`
  4. **Paste:** Send `Shift+Insert` via `evdev`.
  5. **Wait:** `time.sleep(CLIPBOARD_RESTORE_DELAY_SEC)`
  6. **Restore:** Restore OS clipboard to backup.
  7. **Clear:** Empty internal buffer.

### Non-Functional Requirements
- **Thread Safety:** The injector will be called from the `main.py` consumer thread. It must safely block during the `CLIPBOARD_RESTORE_DELAY_SEC` without deafening the separate `sounddevice` capture thread.
- **Dependency:** Add `pyperclip` to manage cross-platform clipboard fetching/setting easily, or utilize native `xclip`/`wl-clipboard` via Python's `subprocess`.

---

## 10. Code Quality Standards & Best Practices

- [ ] **Type Hints:** Ensure `ClipboardInjector` class variables (like `self.buffer`) are fully typed.
- [ ] **Logging:** Use `utils.get_logger(__name__)` for all state changes (e.g., `logger.info("Executing Ideal Flush...")`).
- [ ] **Exception Handling:** If `pyperclip` fails to grab the clipboard, the injector should gracefully fail or proceed with an empty backup rather than crashing the app.

---

## 11. Implementation Plan

### Phase 1: Configuration Updates
**Goal:** Add tuning parameters to `config.py`.
- [x] **Task 1.1:** Add tuning constants: `IDEAL_FLUSH_WORD_COUNT = 25`, `FAILSAFE_FLUSH_MULTIPLIER = 1.6`, `CLIPBOARD_RESTORE_DELAY_SEC = 1.0`. ✓ 2026-04-06
- [x] **Task 1.2:** Update `InjectionMethod` Enum to include `CLIPBOARD` and explicitly set `ACTIVE_INJECTION_METHOD = InjectionMethod.CLIPBOARD` in `config.py` so the user can easily toggle between methods. ✓ 2026-04-06

### Phase 3: Implement Clipboard Engine
**Goal:** Create the `ClipboardInjector` logic.
- [x] **Task 3.1:** Create `text_injection/clipboard_engine.py` extending `BaseInjector`. ✓ 2026-04-06
- [x] **Task 3.2:** Implement `.inject(text: str)` to accumulate text in `self.buffer`. ✓ 2026-04-06
- [x] **Task 3.3:** Implement the flush condition checks (Ideal and Failsafe) inside `.inject()`. ✓ 2026-04-06
- [x] **Task 3.4:** Implement `.flush()` to execute the Ghost Paste Prevention Sequence using `pyperclip` and `evdev` for `Shift+Insert`. ✓ 2026-04-06

### Phase 4: Factory & Main Loop Integration
**Goal:** Ensure the app routes text to the new engine and handles the Cleanup Flush.
- [x] **Task 4.1:** Update `text_injection/manager.py` to instantiate `ClipboardInjector`. ✓ 2026-04-06
- [x] **Task 4.2:** Update `main.py`'s consumer loop. When `utils.is_listening` becomes `False` and the queue is empty, call `injector.flush()` to execute the Cleanup Flush (Trigger 3) before exiting. ✓ 2026-04-06

### Phase 5: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks.
- [x] **Task 5.1:** Install `pyperclip` (`pip install pyperclip`). ✓ 2026-04-06
- [x] **Task 5.2:** Verify syntax and imports. ✓ 2026-04-06

### Phase 6: Manual Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and wait for user manual review.
