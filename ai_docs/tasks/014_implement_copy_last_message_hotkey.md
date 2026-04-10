# Linux Voice-Typing Task: Implement Copy Last Message Hotkey

## 1. Task Overview

### Task Title
**Title:** Implement Copy Last Message Hotkey (`Super+H`)

### Goal Statement
**Goal:** Add a global hotkey (`Super+H`) that fetches the last voice-typed message from the history and copies it directly to the system clipboard.

## 4. Context & Problem Definition

### Problem Statement
Currently, to copy the last voice-typed message, the user must manually navigate through the UI history viewer. There is no quick way to copy the last dictated message using just the keyboard.

### Success Criteria
- [ ] A new configurable hotkey (`HOTKEY_COPY_LAST`) is added to `config.json` and `config.py` with a default of `<cmd>+h`.
- [ ] A new utility function in `utils.py` handles copying text to the clipboard (using `pyperclip`).
- [ ] Pressing `Super+H` successfully fetches the last message from `history/history.py` and copies it to the clipboard.
- [ ] The hotkey listener in `ui/hotkeys.py` registers and responds to the new hotkey.

## 10. Code Quality Standards & Best Practices

- **Function Inspection:** Always inspect function definitions before calling.
- **Type Hints:** Complete type annotations for all new functions and variables.
- **Thread-Safe Rule:** Ensure operations are thread-safe if interacting with global state.
- **Relative Imports:** Always use relative imports (`.`) for internal modules where applicable.

## 11. Implementation Plan

### Phase 1: Configuration Updates
**Goal:** Add the new hotkey setting to the configuration system.
- [x] ✓ 2026-04-10 11:17 **Task 1.1:** Add `HOTKEY_COPY_LAST` to `config.json` and `config.py`.
  - Files: `config.json` (via `config.py` default generation), `config.py`
  - Details: Add `"HOTKEY_COPY_LAST": "<cmd>+h"` to `_DEFAULT_CONFIG` and expose `HOTKEY_COPY_LAST` globally.

### Phase 2: Utility & History Integration
**Goal:** Create a function to fetch the last message and copy it.
- [x] ✓ 2026-04-10 11:18 **Task 2.1:** Create `copy_last_message_to_clipboard()` function in `utils.py`.
  - Files: `utils.py`
  - Details: Import `get_recent_history` from `history`, fetch the last message, and use `pyperclip` to set the clipboard content. Use `logger.info` to log the copy action.

### Phase 3: Hotkey Listener Update
**Goal:** Bind the hotkey to the new utility function.
- [x] ✓ 2026-04-10 11:19 **Task 3.1:** Update `ui/hotkeys.py` to listen for `HOTKEY_COPY_LAST`.
  - Files: `ui/hotkeys.py`
  - Details: Add an `on_activate_copy_last()` function. Add `config.HOTKEY_COPY_LAST` to the `hotkeys` dictionary in `start_hotkey_listener()`. Use `_suppress_typed_character()` just like other hotkeys.

### Phase 4: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks
- [x] ✓ 2026-04-10 11:20 **Task 4.1:** Code Quality Verification
  - Files: All modified files
- [x] ✓ 2026-04-10 11:20 **Task 4.2:** Import and Syntax Validation

### Phase 5: Manual Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and wait for user manual review
- [ ] **Task 5.1:** Present Implementation Complete Message (MANDATORY)
- [ ] **Task 5.2:** Final Manual Verification (By User)

---
**Time Estimate:** 15-20 minutes
