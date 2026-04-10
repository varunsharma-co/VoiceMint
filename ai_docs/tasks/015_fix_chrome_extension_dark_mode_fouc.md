# Linux Voice-Typing Task Template

## Problem
When opening the Chrome extension popup, the UI briefly flashes in light mode before switching to dark mode (if dark mode was previously selected). This Flash of Unstyled Content (FOUC) happens because the theme is loaded asynchronously via `chrome.storage.local`.

## Solution
Use a synchronous `<script>` tag at the beginning of `popup.html`'s `<body>` to read the theme synchronously from `localStorage` and immediately apply the `dark-mode` class to the `document.body`. Update `popup.js` to sync the theme to `localStorage` alongside `chrome.storage.local`.

## Implementation
- [x] ✓ 2026-04-10 12:34 **Task 1:** Create synchronous theme initialization script.
  - Files: `chrome_extension/theme-init.js`
  - Details: Write a tiny script that reads `voice_mint_theme` from `localStorage` and applies `.dark-mode` to `document.body` if it is set to "dark".
- [x] ✓ 2026-04-10 12:34 **Task 2:** Update popup HTML to load the init script.
  - Files: `chrome_extension/popup.html`
  - Details: Add `<script src="theme-init.js"></script>` right after the opening `<body>` tag.
- [x] ✓ 2026-04-10 12:34 **Task 3:** Update popup JS to manage `localStorage`.
  - Files: `chrome_extension/popup.js`
  - Details: Modify `toggleTheme` to save to `localStorage`. Update initialization to rely on the already applied theme or remove the async theme application that causes the flash.

## Files to Modify
- `chrome_extension/theme-init.js` (New)
- `chrome_extension/popup.html` - Add blocking script tag.
- `chrome_extension/popup.js` - Update theme storage logic.

**Time Estimate:** 15 minutes
