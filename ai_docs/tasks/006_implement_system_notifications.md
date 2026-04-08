# Linux Voice-Typing Task Template

## 1. Task Overview

### Task Title
**Title:** Implement GTK3 System Tray, Notifications, and Asset RAM Caching

### Goal Statement
**Goal:** Replace the planned `pystray` library with a native Linux `PyGObject` (AppIndicator3) system tray with a right-click menu. Integrate native `notify-send` notifications and non-blocking `aplay` audio feedback for STT activation/deactivation events. To optimize performance, all UI and audio assets will be loaded into RAM (`/dev/shm`) upon startup with a clean-up hook upon exit.

---

## 2. Existing Codebase Analysis

### Existing Services & Modules Analysis
- **Main Thread**: The architecture dictates that the main thread should run the tray event loop. Since we are moving to `PyGObject`, `gi.repository.Gtk.main()` will run on the main thread. 
- **Assets**: 4 files exist in `assets/`: `icon-off-128.png`, `icon-on-128.png`, `start.wav`, and `stop.wav`.
- **State Changes**: The global state flag `utils.is_listening` controls the STT state. The hotkey listener currently modifies this state.
- **Facade Pattern**: `ui/__init__.py` currently only exports `launch_ui` and `start_hotkey_listener`.

### Current Workflow Understanding
```
Current Flow: App starts -> initializes components -> starts Tkinter on a separate thread -> main thread should run tray loop.
State Operations: When `is_listening` is toggled via hotkey, the tray icon needs to react.
Output/Response: Update AppIndicator icon, trigger `notify-send`, play `.wav` via `aplay`.
```

### Integration vs New Code Decision
- **Integrate**: We will implement the tray logic entirely within `ui/tray.py` and expose an initialization and state-update function via `ui/__init__.py`. 
- **Dependencies**: Native PyGObject (`gi`) requires system packages (`sudo apt install python3-gi gir1.2-appindicator3-0.1`).

---

## 3. Strategic Analysis & Solution Options

### Problem Context
We need a robust Linux system tray application using GTK3 that handles state updates triggered by background threads safely, along with memory-mapped assets.

### Solution Options Analysis

#### Option A: Centralized Tray Manager in `ui/tray.py`
**Approach:** Create a singleton-like `TrayManager` in `ui/tray.py` that handles the RAM asset copying, GTK initialization, notifications, and audio playback. Expose `update_state(active: bool)` to be called by the hotkey listener or main script, ensuring it uses `GLib.idle_add` for thread safety.
**Pros:**
- ✅ Encapsulates all GTK, audio, and notification logic.
- ✅ Ensures `GLib.idle_add` is used centrally.
**Cons:**
- ❌ Slightly complex initialization flow to ensure RAM files are cleaned up on `atexit`.

### Recommendation & Rationale
**RECOMMENDED SOLUTION:** Option A
Centralizing the tray and notification logic cleanly abstracts the GTK complexities away from `main.py` and the hotkeys.

---

## 4. Context & Problem Definition

### Problem Statement
The VoiceMint application currently lacks a visual system tray presence and audio/visual feedback when voice typing is toggled. We need native integration into Linux Mint's Cinnamon panel with RAM-optimized assets to ensure zero-latency feedback without disk I/O bottlenecks.

### Success Criteria
- [ ] GTK AppIndicator3 tray icon displays correctly with a "Quit/Exit" menu.
- [ ] 4 assets are copied to `/dev/shm` on start and deleted on exit.
- [ ] Tray icon updates its state correctly between "off" and "on" using RAM assets (or SSD fallback).
- [ ] `notify-send` issues correct notifications for toggles and duplicate actions.
- [ ] `aplay` plays audio asynchronously.

---

## 5. Development Mode Context

- **Priority: Speed, Zero latency, and minimal CPU/RAM footprint**
- **Aggressive refactoring allowed** - delete/recreate modules as needed.

---

## 6. Technical Requirements

### Functional Requirements
- **Asset Loader**: Copy assets to `/dev/shm/voicemint_assets/` and keep a mapping of available RAM paths vs SSD fallback paths.
- **Tray Icon**: Initialize AppIndicator3. Connect a GTK Menu with "Quit" (which safely shuts down the app).
- **Notifications**: Execute `subprocess.run(["notify-send", ...])` asynchronously.
- **Audio**: Execute `subprocess.Popen(["aplay", ...])` asynchronously.

### Non-Functional Requirements
- **Thread Safety**: Any call to change GTK UI from the hotkey thread MUST use `GLib.idle_add`.
- **Resource Cleanup**: Must hook into `atexit` or the GTK Quit menu to delete `/dev/shm` assets.

---

## 7. State & Persistence

### Global State Management
- Observe `utils.is_listening`. The tray module will keep a localized `current_state` to detect redundant toggle requests (e.g., activating when already active) to issue the appropriate notification.

---

## 8. Code Organization & File Structure

### Files to Modify
- `ui/tray.py`: Core implementation of TrayManager.
- `ui/__init__.py`: Expose TrayManager.
- `main.py`: Initialize the tray and run `Gtk.main()` on the main thread. Hook cleanup logic.

---

## 9. Code Quality Standards & Best Practices

- [ ] **Type Hints:** Complete type annotations for all functions.
- [ ] **Thread-Safe UI Rule:** Explicitly use `GLib.idle_add` for GTK updates.
- [ ] **Context Manager Rule:** Use `subprocess.Popen` carefully to prevent zombie processes.
- [ ] **NO FALLBACK BEHAVIOR**: Raise exceptions if GTK cannot be initialized.

---

## 10. Implementation Plan

### Phase 1: Asset RAM Management
**Goal:** Implement the logic to copy assets to `/dev/shm` and clean them up.
- [x] ✓ 2026-04-07 20:58 **Task 1.1:** Create `ui/tray.py` asset loading and cleanup functions.
  - Files: `ui/tray.py`
  - Details: Implement `load_assets_to_ram()` and `cleanup_ram_assets()`.

### Phase 2: GTK Tray & Notifications
**Goal:** Implement the GTK AppIndicator, menu, `notify-send`, and `aplay` logic.
- [x] ✓ 2026-04-07 20:58 **Task 2.1:** Implement `TrayManager` class.
  - Files: `ui/tray.py`
  - Details: Init AppIndicator, setup menu, implement `toggle_state(active: bool)`, `_show_notification()`, `_play_sound()`.

### Phase 3: Integration
**Goal:** Integrate the tray into the app lifecycle.
- [x] ✓ 2026-04-07 20:58 **Task 3.1:** Hook TrayManager into `main.py` and `ui/__init__.py`.
  - Files: `ui/__init__.py`, `main.py`, `ui/hotkeys.py` (if applicable)
  - Details: Start `Gtk.main()` on the main thread. Update state from hotkeys.

### Phase 4: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks
- [x] ✓ 2026-04-07 20:58 **Task 4.1:** Code Quality Verification
- [x] ✓ 2026-04-07 20:58 **Task 4.2:** Import and Syntax Validation

### Phase 5: Manual Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and wait for user manual review
- [ ] **Task 5.1:** Present Implementation Complete Message (MANDATORY)
- [ ] **Task 5.2:** Final Manual Verification (By User)

---
_Template Version: 3.2 - Linux Voice Typing Optimized_
