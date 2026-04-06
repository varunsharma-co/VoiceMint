# 001 Implement STT Providers

## 1. Task Overview

### Task Title
**Title:** Implement STT Providers and Audio Capture Engine

### Goal Statement
**Goal:** Port the old monolithic STT logic into the new modular architecture. Divide responsibilities between the audio hardware thread (`stt/mic.py`), the watchdog timer thread (`stt/silence.py`), and the STT WebSocket providers via a Facade Pattern (`stt/stt_providers/manager.py`) to ensure zero-latency and clean threading.

---

## 3. Strategic Analysis & Solution Options

### Problem Context
The old Voice-Typing App tangled audio hardware (`sounddevice`), network logic (WebSockets), and application state (crashes via `KeyboardInterrupt`) together inside each provider class. We need to decouple these to support a robust, concurrent architecture.

### Solution Options Analysis

#### Option A: Decoupled Mic Loop with Central State
**Approach:** 
1. `mic.py` exclusively owns the `sounddevice` stream and passes audio byte chunks to an active `BaseTranscriber`.
2. `config.is_listening` (`threading.Event`) controls the lifecycle of both the mic loop and the WebSocket connection.
3. `silence.py` operates as a daemon thread timer that clears `is_listening` upon timeout.
4. `manager.py` handles the provider instantiation.

**Pros:**
- ✅ Clean separation of hardware and network.
- ✅ Thread-safe shutdown across the entire app when `is_listening` is cleared.

**Cons:**
- ❌ Requires careful queue and audio chunk synchronization.

**Implementation Complexity:** Medium - Thread management and WebSocket sync required.
**Risk Level:** Low - Proven architecture for audio pipelines.

### Recommendation & Rationale
**🎯 RECOMMENDED SOLUTION:** Option A - Decoupled Mic Loop with Central State
This directly satisfies the architectural constraints laid out in the Single Source of Truth, ensuring that the app remains lightweight, modular, and thread-safe.

### Decision Request
**👤 USER DECISION REQUIRED:**
Based on this analysis, do you want to proceed with the recommended solution (Option A)?

---

## 4. Context & Problem Definition

### Problem Statement
The application requires a robust method to capture audio, send it to streaming APIs (Soniox, Deepgram, AssemblyAI), and retrieve formatted text. The previous implementation was tightly coupled and prone to hard crashes.

### Success Criteria
- [ ] `stt/mic.py` successfully captures audio and streams it to the active provider.
- [ ] `stt/silence.py` correctly triggers a shutdown after a specified timeout period of silence.
- [ ] STT Providers only process the network WebSocket side and push `is_final=True` transcripts to a queue.
- [ ] A clean exit mechanism is achieved by clearing the `is_listening` threading Event.

---

## 6. Technical Requirements

### Functional Requirements
- STT Providers must implement a `BaseTranscriber` interface.
- Transcripts must be pushed to a thread-safe `queue.Queue`.
- The system must correctly ignore non-final/interim transcripts to prevent double-typing.

### Non-Functional Requirements
- **Latency:** Max 500ms from speech to injection.
- **Resource Usage:** CPU/RAM footprint must be extremely minimal.
- **Thread Safety:** Strict use of `threading` module, avoiding `multiprocessing`.

### Technical Constraints
- The microphone must be managed within a `with sd.InputStream():` context manager.

---

## 8. STT Providers & WebSockets

### WebSocket Lifecycle
- [ ] **Handshakes:** Soniox configuration needs to be implemented. (Deepgram and AssemblyAI later).
- [ ] **Audio Chunking:** Push chunked bytes from `mic.py` into the WebSocket loop.
- [ ] **Interim Transcript Filtering:** Only transcripts with `is_final` flag enabled should be enqueued.

### Queue Logic
- [ ] **Producer/Consumer:** STT Providers push finalized text into a thread-safe `queue.Queue`.

---

## 10. Code Quality Standards & Best Practices

### Python Code Quality Requirements
- [ ] **Type Hints:** Complete type annotations for all functions, classes, and variables.
- [ ] **Context Manager Rule:** Mandate `with sd.InputStream()` to ensure OS hardware is properly released.
- [ ] **🚨 RELATIVE IMPORTS:** Always use relative imports (`.`) for internal modules within the package.
- [ ] **🚨 NO FALLBACK BEHAVIOR - Always raise exceptions instead**

---

## 11. Implementation Plan

### Phase 1: Core Interfaces & Config State
**Goal:** Define the shared state and base contracts.
- [x] ✓ 2026-04-05 16:07 **Task 1.1:** Add `is_listening` event and the `Queue` to `utils.py`.
- [x] ✓ 2026-04-05 16:07 **Task 1.2:** Define the `BaseTranscriber` interface in `stt/stt_providers/base.py`.

### Phase 2: Implement STT Providers and Manager
**Goal:** Create the network components.
- [x] ✓ 2026-04-05 16:11 **Task 2.1:** Implement `SonioxTranscriber`. (Deepgram and AssemblyAI will be implemented later).
- [x] ✓ 2026-04-05 16:11 **Task 2.2:** Implement `manager.py` factory and expose via `stt/stt_providers/__init__.py`.

### Phase 3: Hardware Capture & Silence Watchdog
**Goal:** Implement the audio thread and timer.
- [x] ✓ 2026-04-05 16:12 **Task 3.1:** Implement `silence.py` watchdog timer.
- [x] ✓ 2026-04-05 16:12 **Task 3.2:** Implement `mic.py` to stream audio using `sounddevice`.

### Phase 4: Basic Code Validation (AI-Only)
**Goal:** Run basic automated checks.
- [x] ✓ 2026-04-05 16:15 **Task 4.1:** Code Quality Verification. (Passed basic python syntax check)
- [x] ✓ 2026-04-05 16:15 **Task 4.2:** Import and Syntax Validation.

### Phase 5: Comprehensive Code Review (Mandatory)
**Goal:** Present "Implementation Complete!" and execute thorough code review.
- [x] ✓ 2026-04-05 16:19 **Task 5.1:** Present Implementation Complete Message.
- [x] ✓ 2026-04-05 16:19 **Task 5.2:** Execute Comprehensive Code Review.

---

## 15. Deployment & Configuration

### Environment Variables
```bash
# Required in .env
SONIOX_API_KEY=...
DEEPGRAM_API_KEY=...
ASSEMBLYAI_API_KEY=...
```