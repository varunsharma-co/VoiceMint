# Linux Voice-Typing Task Template

## 1. Task Overview

**Title:** Implement Session History Saving

**Goal:** Create a module to buffer and save the finalized text of voice typing sessions to a local `history.json` file. The application must retain the last `N` (configurable, default 5) session texts. Instead of saving immediately after every session, it will buffer the sessions in memory and write them to disk on a configurable interval (e.g., every 30 minutes) or immediately upon application exit/crash (hard flush).

---

## 3. Strategic Analysis & Solution Options

### Problem Context
The user requested a feature to save the transcript of complete voice typing sessions. To minimize disk I/O, these saves should be delayed. Sessions completed within a 30-minute window should be buffered in memory and written to `history.json` together. In the case of a hard exit or crash, any unsaved sessions must be forcefully flushed to disk.

### Solution Options Analysis

#### Option 1: Background Timer + atexit Hook (Recommended)
**Approach:** The `queue_consumer` thread accumulates text for a session. When the session ends, the full text is appended to a thread-safe global list of "pending sessions" in memory. A background daemon thread (or `threading.Timer`) runs every 30 minutes to check this list; if it contains new sessions, it appends them to `history.json`, truncates to the last 5, and clears the list. An `atexit` hook ensures the same flush logic runs if the app exits before the timer fires.
**Pros:**
- ✅ Minimizes disk I/O by batching writes.
- ✅ `atexit` ensures no data loss on graceful exits or standard crashes.
- ✅ Clean separation of concerns (consumer handles sessions, timer handles file I/O).
**Cons:**
- ❌ Slightly more complex due to the background timer thread.

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option 1 - Using an `atexit` hook combined with a background timer ensures that we meet both the delayed writing requirement and the "no data loss on crash/exit" requirement.

---

## 4. Context & Problem Definition

### Problem Statement
Currently, voice typed transcripts are injected into the OS but not saved anywhere. We need a way to review recent dictations, saved efficiently in batches.

### Success Criteria
- [ ] Add `MAX_HISTORY_MESSAGES = 5` and `HISTORY_SAVE_INTERVAL_MINUTES = 30` to `config.py`.
- [ ] Create a `history.py` file with logic to read, append, truncate (to 5), and save JSON data in batches.
- [ ] Update `main.py` to accumulate `is_final` text during the session and add completed sessions to a memory buffer.
- [ ] Implement a background task that flushes the pending list to `history.json` every 30 minutes.
- [ ] Implement an `atexit` hook to perform a hard flush of pending sessions on exit.
- [ ] The `history.json` file is properly formatted as a JSON array of strings.

---

## 6. Technical Requirements

### Functional Requirements
- **Configuration:** `config.py` holds the maximum history count and the save interval.
- **History Module:** Exposes a `flush_history()` function that writes any buffered sessions to disk.
- **Session Tracking:** The consumer thread must recognize when a session ends and add its accumulated text to the history buffer.
- **Background Timer:** A recurring daemon thread that calls `flush_history()` every 30 minutes.
- **Hard Flush:** Uses Python's `atexit` module to register `flush_history` so it runs automatically when the script terminates.

### Non-Functional Requirements
- **Thread Safety:** The memory buffer (e.g., a `queue.Queue` or a lock-protected list) must be safely accessed by both the consumer thread and the timer/atexit thread.
- **Resource Usage:** I/O operations strictly occur only on the 30-minute interval or at exit.

---

## 10. Code Quality Standards & Best Practices

- [ ] **Type Hints:** Ensure function definitions use clear type hints.
- [ ] **Logging:** Log the history save events using `utils.get_logger(__name__)`.
- [ ] **Exception Handling:** Gracefully handle corrupted or unreadable `history.json` files by overwriting them with a fresh array.

---

## 11. Implementation Plan

### Phase 1: Configuration & History Module
**Goal:** Define config settings and build the file I/O logic.
- [x] **Task 1.1:** Add `MAX_HISTORY_MESSAGES = 5` and `HISTORY_SAVE_INTERVAL_MINUTES = 30` to `config.py`. ✓ 2026-04-06
- [x] **Task 1.2:** Create `history.py` with the thread-safe pending sessions buffer, the `flush_history()` function, and the `atexit.register(flush_history)` hook. ✓ 2026-04-06

### Phase 2: Consumer Thread & Timer Integration
**Goal:** Accumulate text, trigger the history buffer, and start the timer.
- [x] **Task 2.1:** Update `main.py` `queue_consumer` to append incoming text to a `session_text` string, and when the session ends, push it to the history buffer. ✓ 2026-04-06
- [x] **Task 2.2:** Add logic to start the 30-minute recurring background timer that calls `flush_history()`. ✓ 2026-04-06

### Phase 3: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks.
- [x] **Task 3.1:** Verify syntax and imports. ✓ 2026-04-06

### Phase 4: Manual Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and wait for user manual review.