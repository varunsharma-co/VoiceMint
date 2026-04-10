# Linux Voice-Typing Task Template

## 1. Task Overview

### Task Title
**Title:** Implement AssemblyAI Streaming Speech-to-Text Provider

### Goal Statement
**Goal:** Add a new `AssemblyAITranscriber` class to handle real-time streaming speech-to-text using AssemblyAI's WebSocket API, integrating it smoothly into the existing `stt_providers` module without changing the default STT provider.

---

## 2. 🟡🔴 MANDATORY: Existing Codebase Analysis

### Existing Services & Modules Analysis

- **Project Structure Discovery:** The streaming STT handlers are located in `stt/stt_providers/`. There is a `BaseTranscriber` base class, a `SonioxTranscriber` implementation, and a `manager.py` factory function.
- **Thread-Specific Logic Discovery:** 
  - Audio capture and WebSocket sending happen from the audio thread managed in `mic.py`.
  - The provider receives audio via `send_audio_chunk`.
  - The provider runs a background daemon thread for `_message_handler` that listens to WebSocket messages and calls the `callback`.
- **Current Workflow:** `start_listening()` gets the transcriber via `get_transcriber`, starts connection, opens `sounddevice` stream, and sends bytes continuously.
- **Integration vs New Code Decision:** We will create a new module `stt/stt_providers/assembly.py` mimicking the pattern established by `soniox.py`, and extend `manager.py` to route `STTProvider.ASSEMBLYAI` to this new class.

### 🚨 INTEGRATION REQUIREMENTS
- **Files to Modify:** `stt/stt_providers/manager.py`, `stt/stt_providers/assembly.py`
- **Dependencies to Add:** None (We'll use the existing `websockets` library).

---

## 3. 🟡🔴 Strategic Analysis & Solution Options

### Problem Context
The user wants to add AssemblyAI as an alternative STT provider without making it the default. We need to use their WebSocket API instead of their Python SDK to keep dependencies lean and utilize the existing `websockets.sync.client` connection paradigm.

### Solution Options Analysis

**Option 1: Implement using `websockets.sync.client` (Recommended)**
- **Approach:** Create `AssemblyAITranscriber` inheriting from `BaseTranscriber`. Use `connect()` with the `Authorization` header and send binary audio data. Read JSON responses in a loop.
- **Pros:** Matches the `SonioxTranscriber` structure, keeps dependencies zero, thread-safe.
- **Cons:** Manual WebSocket handling instead of the official SDK.

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option 1
The project already utilizes `websockets` for Soniox. Keeping this consistent prevents bloat.

### Decision Request
**👤 USER DECISION REQUIRED:**
Based on this analysis, do you want to proceed with the recommended solution (Option 1)?

---

## 4. Context & Problem Definition

### Problem Statement
The app needs to support AssemblyAI as an STT provider using a direct WebSocket connection, capturing audio with `sounddevice` and bypassing the Python SDK, while ensuring it fits the project's Facade pattern.

### Success Criteria
- [ ] `AssemblyAITranscriber` class created and functioning.
- [ ] `manager.py` returns an AssemblyAI instance when configured.
- [ ] Only `message_type == 'FinalTranscript'` (or equivalent) messages are forwarded to the queue.
- [ ] No changes to the default provider in `config.py`.

---

## 6. 🟡🔴 Technical Requirements

### Functional Requirements
- Initialize connection to AssemblyAI realtime endpoint (`wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000`) with `Authorization` header.
- Send binary PCM 16-bit 16kHz audio data.
- Read JSON responses. If `message_type == "FinalTranscript"`, push `text` to callback with `is_final=True`.

### Non-Functional Requirements
- Thread Safety: Ensure connection closing and message thread termination do not block.

---

## 8. 🟡🔴 STT Providers & WebSockets

### WebSocket Lifecycle
- **Handshakes:** Pass `Authorization` header during connect.
- **Audio Chunking:** Push chunked bytes.
- **Interim Transcript Filtering:** Discard partial transcripts to prevent duplicates.

---

## 10. Code Quality Standards & Best Practices

- Use relative imports.
- Proper early returns and exception handling.

---

## 11. Implementation Plan

### Phase 1: Create AssemblyAI Transcriber
**Goal:** Implement the new transcriber class.
- [x] **Task 1.1:** Add logic to `stt/stt_providers/assembly.py` (✓ 2026-04-10)
  - Inherit from `BaseTranscriber`.
  - Use `websockets.sync.client.connect(url, additional_headers={"Authorization": self.api_key})`.
  - Extract final transcripts and call `self.callback(text, True)`.

### Phase 2: Integrate with Manager
**Goal:** Hook up the new transcriber in the factory.
- [x] **Task 2.1:** Update `stt/stt_providers/manager.py` (✓ 2026-04-10)
  - Import `AssemblyAITranscriber` from `.assembly`.
  - Update logic for `STTProvider.ASSEMBLYAI` to return the new instance.

### Phase 3: Basic Code Validation (AI-Only)
- [x] **Task 3.1:** Code Quality Verification (✓ 2026-04-10)
- [x] **Task 3.2:** Import and Syntax Validation (✓ 2026-04-10)

### Phase 4: Manual Code Review (Mandatory)
- [ ] **Task 4.1:** Present Implementation Complete Message
- [ ] **Task 4.2:** Final Manual Verification (By User)

---

## 15. 🔴 Deployment & Configuration

### Environment Variables
```bash
# Needs to be configured in .env for users who use AssemblyAI
ASSEMBLYAI_API_KEY=your-secret-key
```

---

## 17. AI Agent Instructions

**Files to be Edited:**
- `stt/stt_providers/assembly.py`
- `stt/stt_providers/manager.py`

**👤 How would you like to proceed?**
**A) Preview Detailed Code Changes**
**B) Approve and Start Implementation**
**C) Modify the Approach**