# Linux Voice-Typing Task Template

## 1. Task Overview

**Title:** Implement UInput Text Injection Engine

**Goal:** Create a standardized, extensible text injection system that uses Linux `evdev` (uinput) to simulate rapid keyboard events for injecting speech-to-text results at the active cursor position.

---

## 3. Strategic Analysis & Solution Options

### Problem Context
The application needs a reliable way to inject transcribed text into the OS. Multiple injection methods might be supported in the future (e.g., Clipboard, XDO Tool, iBus). Thus, the application requires a robust manager and a base class structure.

### Solution Options Analysis

#### Option 1: Direct Evdev Injection (UInput)
**Approach:** Create an `evdev` UInput device that simulates literal keypresses at hardware speeds.
**Pros:**
- ✅ Extremely fast and zero-latency
- ✅ Works natively on Wayland and X11 at the kernel level
- ✅ Bypasses clipboard interference

**Cons:**
- ❌ Requires `udev` input group permissions or `sudo` to access `/dev/uinput`
- ❌ Must manually manage `Shift` keys for capital letters and map characters to scancodes

**Implementation Complexity:** Medium - Requires character-to-scancode mapping and shift state management.
**Risk Level:** Medium - Permission errors if the user lacks `/dev/uinput` access.

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option 1 - Direct Evdev Injection (UInput)
As tested in the provided prototype, `evdev` perfectly matches the core architectural requirement of high-speed native typing. A base class will ensure future scalability to clipboard or other engines.

---

## 4. Context & Problem Definition

### Problem Statement
We need an extensible text injection module that pulls transcripts from the internal queue and fires real keyboard scancodes to type them globally.

### Success Criteria
- [ ] A `BaseInjector` abstract class is created.
- [ ] A `UInputInjector` implements the injection logic using `evdev`.
- [ ] A Manager file provides the active injector based on configuration.
- [ ] The `config.py` correctly defines the `ACTIVE_INJECTION_METHOD`.

---

## 6. Technical Requirements

### Functional Requirements
- **Manager:** The `manager.py` exposes a `get_injector()` factory function.
- **UInput Engine:** The `uinput_engine.py` maps strings into `evdev.ecodes` and correctly handles shift states for capitalization.

### Non-Functional Requirements
- **Latency:** Zero latency; characters must be injected with minimal sleep (0.01s).
- **Extensibility:** The design must cleanly support adding new engines later without modifying core typing logic.

### Technical Constraints
- The `UInput` instance should ideally be created once per session or managed efficiently to avoid OS overhead of repeatedly spawning virtual hardware.
- Only the `UInputInjector` handles the evdev translation logic.

---

## 10. Code Quality Standards & Best Practices

- [ ] **Type Hints:** All functions, classes, and variables must be fully typed.
- [ ] **Context Manager Rule:** Ensure proper `evdev.UInput()` closure.
- [ ] **🚨 RELATIVE IMPORTS:** Use relative imports within the `text_injection` package.
- [ ] **Facade Pattern:** Export `get_injector` through `text_injection/__init__.py`.
- [ ] **No print() for core logic:** Ensure minimal logging via a proper logger instead of standard prints.

---

## 11. Implementation Plan

### Phase 1: Configuration & Base Setup
**Goal:** Define the Enums in config and the ABC in the text injection package.
- [x] **Task 1.1:** Update `config.py` ✓ 2026-04-06
  - Add `InjectionMethod` Enum (`UINPUT`) and set `ACTIVE_INJECTION_METHOD`.
- [x] **Task 1.2:** Implement `text_injection/base.py` ✓ 2026-04-06
  - Create `BaseInjector` class with `inject(self, text: str) -> bool` method and `close(self)` method for cleanup.

### Phase 2: UInput Engine & Manager
**Goal:** Implement the evdev typing engine and factory manager.
- [x] **Task 2.1:** Implement `text_injection/uinput_engine.py` ✓ 2026-04-06
  - Create `UInputInjector` class inheriting from `BaseInjector`.
  - Move the prototype scancode mapping and keypress simulation into the `.inject()` method.
- [x] **Task 2.2:** Implement `text_injection/manager.py` ✓ 2026-04-06
  - Create the factory logic to return a `UInputInjector` instance based on `ACTIVE_INJECTION_METHOD`.
- [x] **Task 2.3:** Expose via `text_injection/__init__.py` ✓ 2026-04-06
  - Export the manager function and injector classes using the facade pattern.

### Phase 3: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks.
- [x] **Task 3.1:** Verify syntax and imports. ✓ 2026-04-06

### Phase 4: Manual Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and wait for user manual review.
