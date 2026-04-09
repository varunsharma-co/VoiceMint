# Linux Voice-Typing Task Template

## 1. Task Overview
**Title:** Implement Session History Viewer in Settings UI
**Goal:** Add a "View Last 3 Messages" feature within the Settings UI's History Tab, displaying recent session history in a modal "Card" layout, and refine the main Settings window's action buttons to include a "Close" option.

## 2. Existing Codebase Analysis
- **Existing Related Modules:**
  - `ui/settings_ui.py` (Contains `SettingsPanel`)
  - `ui/constants.py` (Contains window geometry and constants)
  - `history/history.py` (Contains `_history_buffer` and `flush_history()`)
- **Current Workflow:** The user opens Settings from the system tray. The History tab allows configuring max messages and save interval. History is stored in RAM (`_history_buffer`) before being flushed to `history.json`.
- **Integration Decision:** Extend existing modules. Add a new `HistoryViewerWindow` class to `ui/settings_ui.py` (or as a separate file, but it's tightly coupled to the settings UI, so appending to `settings_ui.py` is fine). Add new constants to `ui/constants.py`. Add a helper to `history/history.py` if needed to fetch the last 3 messages safely, or read directly from the buffer/json. Actually, since `_history_buffer` might not be saved yet, we should read from the JSON and the buffer, or just the JSON. Let's see how `history.py` exposes history.

## 3. Context & Problem Definition
### Problem Statement
Users need a way to quickly review their most recent voice-typed messages and copy them if necessary, without having to locate and open the raw `history.json` file. The settings dialog also needs a non-destructive way to close without saving changes.
### Success Criteria
- [ ] `HISTORY_WINDOW_GEOMETRY` and `MIN_HISTORY_WINDOW_SIZE` added to constants.
- [ ] History tab has a separator and "View Last 3 Messages" button.
- [ ] Settings bottom buttons are side-by-side: "Save & Exit" and "Close", centered above the restart warning.
- [ ] `HistoryViewerWindow` displays up to 3 recent messages in a "Card" layout.
- [ ] Messages are displayed in read-only, scrollable text boxes.
- [ ] "Copy" button works, updating to "Copied!" temporarily.

## 4. Development Mode Context
- **Priority: Speed, Zero latency, and minimal CPU/RAM footprint**
- **Aggressive refactoring allowed** - delete/recreate modules as needed
- **🚨 CRITICAL: Fix Root Problems, Don't Work Around Them**

## 10. Code Quality Standards & Best Practices
- [ ] Thread-Safe UI Rule: Use `.after()` for UI updates like "Copied!" reverting to "Copy".
- [ ] Function Inspection: Verify parameter types before calling.

## 11. Implementation Plan
### Phase 1: Update UI Constants
- [x] **Task 1.1:** Update `ui/constants.py` ✓ 2026-04-09
  - Details: Add `HISTORY_WINDOW_GEOMETRY = "550x450"` and `MIN_HISTORY_WINDOW_SIZE = (550, 450)`. Add `GLOBAL_FONT` and `BUTTON_FONT` if they don't exist, though `APP_FONT` might exist.

### Phase 2: Update Settings Bottom Buttons
- [x] **Task 2.1:** Update `ui/settings_ui.py` (`SettingsPanel._setup_ui`) ✓ 2026-04-09
  - Details: Change the bottom frame to use a center container frame for "Save & Exit" and "Close".

### Phase 3: Implement History Viewer Window
- [x] **Task 3.1:** Create `HistoryViewerWindow` class in `ui/settings_ui.py` ✓ 2026-04-09
  - Details: Use `HISTORY_WINDOW_GEOMETRY`. Read from `history/history.json` (or expose a `get_recent_history()` in `history.py`). Implement the Card layout.
- [x] **Task 3.2:** Update `SettingsPanel._build_history_tab` ✓ 2026-04-09
  - Details: Add separator and button to launch `HistoryViewerWindow`.

### Phase 4: Manual Code Review (Mandatory)
- [x] **Task 4.1:** Present Implementation Complete Message (MANDATORY) ✓ 2026-04-09
- [ ] **Task 4.2:** Final Manual Verification (By User)
