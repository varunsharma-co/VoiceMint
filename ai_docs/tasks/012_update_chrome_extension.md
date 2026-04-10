# Task 012: Update Chrome Extension UI and Persistence

## 1. Task Overview

### Task Title
**Title:** Update Chrome Extension UI, State Persistence, and Shortcuts

### Goal Statement
**Goal:** Enhance the VoiceMint Chrome extension with per-tab state persistence, improved UI (copy icon placement, font sizes, reset button), updated LLM provider naming, and a new keyboard shortcut (`Ctrl+M`) to open the popup and inject selected text.

---

## 4. Context & Problem Definition

### Problem Statement
The current Chrome extension lacks state persistence across tabs, making it difficult to switch context without losing work. The UI needs refinement to match the "old" extension's UX (copy button inside textarea, reset button). Additionally, the keyboard shortcut needs to be more intuitive and functional (auto-injecting selected text).

### Success Criteria
- [ ] Extension icon in URL bar uses `icon-on-128.png` (or consistent active/inactive state).
- [ ] "VoiceMint" header font size increased.
- [ ] Copy icon is positioned inside the textarea (top or bottom right).
- [ ] Heading "Choose a Format Provider" changed to "Choose the LLM".
- [ ] Gemini model displayed as "Gemini Flash 2.5 Lite".
- [ ] Extension state (input/output/selections) persists per tab using `chrome.storage.session`.
- [ ] Reset button added to header to clear state for the current tab.
- [ ] Keyboard shortcut `Ctrl+M` opens the popup and injects selected text from the page into the input box.
- [ ] If no text is selected, the popup shows the previous state for that tab.

---

## 5. Development Mode Context

- **Priority:** Speed, Zero latency, and minimal CPU/RAM footprint.
- **Aggressive refactoring allowed.**

---

## 7. 🟡 State & Persistence

### Global State Management
- Use `chrome.storage.session` to store a mapping of `tabId` to state objects.
- State object includes: `transcript_output`, `formatted_output`, `selected_prompt`, `selected_provider`.

---

## 10. Code Quality Standards & Best Practices

- [ ] **Type Hints:** Complete type annotations for all JS functions if using JSDoc.
- [ ] **Thread-Safe UI Rule:** Non-applicable for extension popup, but ensure async operations don't block.
- [ ] **Relative Imports:** Use relative paths for extension assets.

---

## 11. Implementation Plan

### Phase 1: UI and Assets
**Goal:** Update icons, headings, and basic styling.

- [x] **Task 1.1:** Update `manifest.json` icons and action default icon. ✓ 2026-04-10 09:38
  - Files: `chrome_extension/manifest.json`
- [x] **Task 1.2:** Increase header font size and change headings. ✓ 2026-04-10 09:38
  - Files: `chrome_extension/popup.html`, `chrome_extension/popup.css`
- [x] **Task 1.3:** Add Reset button to header. ✓ 2026-04-10 09:38
  - Files: `chrome_extension/popup.html`, `chrome_extension/popup.css`
- [x] **Task 1.4:** Move copy icon inside textarea. ✓ 2026-04-10 09:38
  - Files: `chrome_extension/popup.html`, `chrome_extension/popup.css`

### Phase 2: State Persistence & LLM Names
**Goal:** Implement per-tab persistence and update model naming.

- [x] **Task 2.1:** Implement `chrome.storage.session` for per-tab state. ✓ 2026-04-10 09:45
  - Files: `chrome_extension/popup.js`
- [x] **Task 2.2:** Update Gemini model display name. ✓ 2026-04-10 09:45
  - Files: `chrome_extension/popup.js` (init response handling)
- [x] **Task 2.3:** Add logic for Reset button to clear tab state. ✓ 2026-04-10 09:45
  - Files: `chrome_extension/popup.js`

### Phase 3: Keyboard Shortcut & Auto-Injection
**Goal:** Update shortcut and implement auto-injection of selected text.

- [x] **Task 3.1:** Change suggested key to `Ctrl+M`. ✓ 2026-04-10 09:45
  - Files: `chrome_extension/manifest.json`
- [x] **Task 3.2:** Update `popup.js` to handle selected text injection on open. ✓ 2026-04-10 09:45
  - Files: `chrome_extension/popup.js`

### Phase 4: Bug Fixes & Refinements
**Goal:** Fix state reset bug and restore theme toggle.

- [x] **Task 4.1:** Fix `restoreState` to prevent overwriting same-selection text. ✓ 2026-04-10 09:55
  - Files: `chrome_extension/popup.js`
- [x] **Task 4.2:** Restore Theme Toggle to header (keep Reset button). ✓ 2026-04-10 09:55
  - Files: `chrome_extension/popup.html`, `chrome_extension/popup.css`, `chrome_extension/popup.js`

### Phase 5: Manual Code Review
🚨 **CRITICAL WORKFLOW CHECKPOINT**
- Present "Implementation Complete!" and wait for user review.

---

## 17. AI Agent Instructions

### Implementation Approach

1. **COMPLEXITY TRIAGE FIRST: 🟡 STANDARD**
2. **ANALYZE EXISTING CODEBASE**
3. **CREATE TASK DOCUMENT**
4. **PRESENT TASK DOCUMENT & IMPLEMENTATION OPTIONS**
5. **IMPLEMENT PHASE-BY-PHASE** (After approval)
