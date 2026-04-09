# Linux Voice-Typing Task: Implement Settings UI & JSON Configuration Architecture

## 1. Task Overview

### Task Title
**Title:** Modernize UI & Refactor Configuration to Single Source of Truth (`config.json`)

### Goal Statement
**Goal:** Overhaul the configuration architecture to use `config.json` as the single source of truth, turning `config.py` into a pure loader module. Simultaneously, completely modernize the raw UI in `ui/floating.py` using a modern `customtkinter` aesthetic (segmented buttons, rounded frames, clean tabviews) and implement a categorized "Settings" panel (`ui/settings_ui.py`) that reads from and writes directly to `config.json`. Saving settings should prompt the user to restart the application.

---

## 2. Existing Codebase Analysis

### Existing Services & Modules Analysis
- **Current UI Thread Logic:** `ui/floating.py` defines `VoiceMintUI` as a simple `ctk.CTk` grid with Start/Stop buttons and an always-on-top toggle. No settings are exposed.
- **Config Flow:** `config.py` currently holds stale hardcoded default variables (`HOTKEY_START`, `ACTIVE_STT_PROVIDER`, `SILENCE_TIMEOUT_SECONDS`, etc.). 
- **State Pattern:** Background workers and UI modules import variables directly from `config` (e.g., `config.HOTKEY_START`). This access pattern must remain intact so we don't have to touch `main.py` or background workers. 

### Integration vs New Code Decision
- **Integration:** Refactor `config.py` to load its state from `config.json` instead of hardcoding variables. Update `ui/floating.py` for a UI overhaul and to add a "Settings" button.
- **New Code:** Create `config.json` in the root directory containing default settings. Create `ui/settings_ui.py` for a new `SettingsPanel` class that uses a categorized `ctk.CTkTabview` to modify `config.json` directly.

---

## 3. Strategic Analysis & Solution Options

### Problem Context
The current `config.py` holds hardcoded defaults, meaning users have no easy way to persist setting changes made in the GUI without editing Python code. We want a single source of truth (`config.json`) that the UI can safely read and rewrite.

### Solution Options Analysis

#### Option 1: Pure JSON Loader (`config.json` as Single Source of Truth)
**Approach:** Move all settings into `config.json`. Refactor `config.py` to read `config.json` on import and bind the values as module-level attributes, maintaining backward compatibility for `from config import SILENCE_TIMEOUT_SECONDS`. The UI directly reads/writes `config.json` and prompts for app restart.
**Pros:**
- ✅ One single source of truth.
- ✅ Zero risk of rewriting Python files dynamically.
- ✅ No changes needed in `main.py` or background thread logic.
**Cons:**
- ❌ App needs to be restarted for some thread-locked settings to apply (which is acceptable and requested).

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option 1 - Pure JSON Loader. This satisfies the requirement for a clean architectural split while ensuring background workers continue accessing `config.*` variables unchanged.

---

## 4. Context & Problem Definition

### Problem Statement
The VoiceMint UI is currently extremely barebones and provides no way for the user to configure the application. Furthermore, `config.py` acts as a hardcoded storage rather than a flexible configuration system. A modern, polished settings panel is needed to allow users to update settings safely without touching Python files.

### Success Criteria
- [ ] Create `config.json` in the root directory with all configurable parameters.
- [ ] Refactor `config.py` to be a pure loader that reads `config.json` and exposes variables at the module level.
- [ ] `ui/floating.py` is overhauled to look modern, clean, and highly polished with CustomTkinter (segmented buttons, rounded frames).
- [ ] A "Settings" button toggles a highly polished settings panel.
- [ ] `ui/settings_ui.py` contains a clean `CTkTabview` categorized into Application, Hotkeys, History, and Clipboard.
- [ ] The Settings UI reads/writes directly to `config.json`.
- [ ] Display Start/Stop hotkeys as `Super + [input]` in the GUI.
- [ ] Provide a "Save Settings" button that updates the JSON and prompts the user to close & restart the app.
- [ ] Do NOT touch `main.py` or core background worker logic.

---

## 6. Technical Requirements

### Functional Requirements
- **Configuration Architecture:** Move all non-secret settings from `config.py` to `config.json`. Enums (`STTProvider`, `InjectionMethod`) remain in `config.py`, but their active state is driven by the string values in `config.json`.
- **UI Architecture:** Use `ctk.CTkTabview` for the Settings Panel.
- **Form Controls:** Use modern CustomTkinter elements: `ctk.CTkOptionMenu` or Segmented Buttons for STT/Injection, `ctk.CTkEntry` for floats/integers/hotkeys.
- **Save & Restart:** When settings are saved, show a `ctk.CTkToplevel` popup or message prompting the user to restart the application.

---

## 7. State & Persistence

### JSON Logic
- **`config.json`:** The singular file for storing the application configuration.
- **Enums serialization:** JSON will store strings (e.g., `"soniox"`), and `config.py` will parse them into `STTProvider` Enum instances upon load so that downstream code continues to receive Enums as expected.

---

## 9. Code Organization & File Structure

### Files to Modify
- `config.py`
- `ui/floating.py`

### New Files to Create
- `config.json`
- `ui/settings_ui.py`

---

## 11. Implementation Plan

### Phase 1: Configuration Architecture Migration
**Goal:** Migrate to the `config.json` single source of truth.
- [x] **Task 1.1:** Create `config.json` with all default variables. ✓ 2026-04-08 13:58
  - Files: `config.json`
- [x] **Task 1.2:** Refactor `config.py` to read `config.json` on import, map string values to Enums where necessary, and expose the variables dynamically. Ensure `main.py` access remains unbroken. ✓ 2026-04-08 13:58
  - Files: `config.py`

### Phase 2: Core UI Overhaul
**Goal:** Modernize `VoiceMintUI` in `ui/floating.py`.
- [x] **Task 2.1:** Redesign grid layout, use rounded frames, update Status indicator, replace standard buttons with modern/segmented buttons. Add a toggle/button to open the Settings Panel. ✓ 2026-04-08 14:02
  - Files: `ui/floating.py`

### Phase 3: Settings Panel Implementation
**Goal:** Build the categorized Settings UI that modifies `config.json`.
- [x] **Task 3.1:** Create `ui/settings_ui.py` defining `SettingsPanel`. Build a clean `CTkTabview` for Application, Hotkeys, History, and Clipboard. ✓ 2026-04-08 14:02
  - Files: `ui/settings_ui.py`
- [x] **Task 3.2:** Implement logic to read from and write back to `config.json`. ✓ 2026-04-08 14:02
- [x] **Task 3.3:** Add an "App Restart Required" prompt upon saving. ✓ 2026-04-08 14:02

### Phase 4: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks
- [x] **Task 4.1:** Code Quality Verification ✓ 2026-04-08 14:03
- [x] **Task 4.2:** Import and Syntax Validation ✓ 2026-04-08 14:03

### Phase 5: Manual Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and wait for user manual review
- [x] **Task 5.1:** Present Implementation Complete Message (MANDATORY) ✓ 2026-04-08 14:04
- [ ] **Task 5.2:** Final Manual Verification (By User)
