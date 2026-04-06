# Linux Voice-Typing Task Template

> **Instructions:** This template helps you create appropriately-sized task documents for AI-driven Python development. **Read the complexity triage below FIRST** to avoid creating unnecessarily verbose documents.

---

## 🎯 TASK COMPLEXITY TRIAGE - READ THIS FIRST

**Choose your task complexity and ONLY fill out the appropriate sections:**

### 🟢 **SIMPLE TASK** (Use sections 1,4,10,11 only - ~150 lines)

**Examples:** Configuration changes, single file updates, adding imports, simple bug fixes, dependency additions
**Sections to use:** Task Overview, Problem Definition, Code Quality Standards, Implementation Plan (includes Task Completion Tracking)
**Skip:** Strategic analysis, codebase analysis, state changes, error handling, impact analysis

### 🟡 **STANDARD TASK** (Use sections 1,3,4,6,8,10,11,15 - ~400 lines)

**Examples:** New features spanning multiple files, thread management logic, STT provider integrations, state management
**Sections to use:** Full analysis but skip the most detailed sections
**Skip:** Deep second-order impact, extensive error handling for simple changes

### 🔴 **COMPLEX TASK** (Use all sections - ~600+ lines)

**Examples:** Core text injection engine updates, architecture overhauls, breaking changes with broad system impact
**Sections to use:** All sections with full detail and analysis

### 🚀 **QUICK-START TEMPLATE** (For 80% of tasks)

```markdown
## Problem

[1-2 sentences describing what's broken/missing]

## Solution

[1-2 sentences describing the fix]

## Implementation

- [ ] **Task 1:** [Specific action]
  - Files: [path/to/file.py]
  - Details: [What to change]
- [ ] **Task 2:** [Specific action]
  - Files: [path/to/file.py]
  - Details: [What to change]

## Files to Modify

- `path/to/file.py` - [What changes]

**Time Estimate:** [X minutes/hours]
```

**👉 For simple tasks, USE THE QUICK-START TEMPLATE ABOVE and skip the rest!**

---

## 1. Task Overview

### Task Title

<!-- Provide a clear, specific title for this task -->

**Title:** [Brief, descriptive title of what you're building/fixing]

### Goal Statement

<!-- One paragraph describing the high-level objective -->

**Goal:** [Clear statement of what you want to achieve and why it matters]

---

## 2. 🟡🔴 MANDATORY: Existing Codebase Analysis (SKIP for 🟢 Simple Tasks)

### When to Use This Section:

✅ **USE:** New features, unfamiliar codebase, cross-thread changes, complex integrations
❌ **SKIP:** Configuration changes, single file updates, simple bug fixes, adding imports

### 🚨 CRITICAL WORKFLOW REQUIREMENT

**⚠️ BEFORE ANY PLANNING OR IMPLEMENTATION: You MUST thoroughly analyze the existing codebase to understand:**

1. **What threads/modules already exist** that handle similar functionality
2. **How the current workflow processes** the audio/text you're working with
3. **Whether this is an extension** of existing code or truly new functionality
4. **What patterns and architectures** (e.g., Facade Pattern) are already established

**🛑 NEVER start planning implementation without this analysis!**

### Existing Services & Modules Analysis

#### Step 1: Project Structure Discovery

```bash
# Commands you MUST run to understand the project:
list_dir("")  # Get overall project structure
list_dir("stt/") or list_dir("text_injection/") or list_dir("ui/")  # Find core sub-packages
```

#### Step 2: Thread-Specific Logic Discovery

**REQUIRED: Search for Thread-specific logic related to your task. For example:**

- If working on audio: Look for `stt/mic.py`, `stt/silence.py` (Audio thread).
- If working on UI: Look for `ui/tray.py`, `ui/floating.py` (UI thread).
- If working on typing: Look for `text_injection/uinput_engine.py` (Injection thread).

**🔍 MANDATORY ANALYSIS QUESTIONS:**

- [ ] What thread topology currently exists (Main, UI, Audio/WS, Injection)?
- [ ] What thread will this new code run on?
- [ ] **How does the current workflow** process similar data/requests?
- [ ] **What patterns are established** for thread safety, hardware interaction, and logging?
- [ ] **Where should new functionality be added** - existing modules or new sub-packages?

#### Step 3: Current Workflow Understanding

**CRITICAL: For your specific task, map out:**

```
Current Flow: [Describe how similar interactions are currently processed]
Entry Point: [Which thread/module receives input]
Processing Steps: [What steps happen in order]
State Operations: [How state flags/JSON history is updated]
Output/Response: [What gets injected or updated in the UI]
```

#### Step 4: Hardware & Facade Inspection (CRITICAL)

**🚨 MANDATORY: Inspect hardware initialization and Facade logic before implementation**

**ALWAYS inspect function definitions to understand:**

- [ ] **Hardware Inspection**: Check for `evdev` device initialization and `/dev/uinput` permission handling.
- [ ] **Facade Check**: Verify `__init__.py` files to ensure new cross-package logic is exposed properly and respects the Facade Pattern.
- [ ] **Parameter types**: What exact types does the function expect?
- [ ] **Return types**: What does the function return?

#### Step 5: Integration vs New Code Decision

**🎯 INTEGRATION DECISION MATRIX:**

**✅ EXTEND EXISTING MODULE WHEN:**

- [ ] Similar functionality already exists in a module
- [ ] The workflow naturally fits into existing processing pipeline
- [ ] Adding new steps to existing methods makes logical sense
- [ ] Maintains consistency with established patterns

**✅ CREATE NEW MODULE WHEN:**

- [ ] Functionality is completely different from existing modules
- [ ] New module would be reusable across multiple workflows
- [ ] Existing modules are already complex and adding more would hurt maintainability

**📋 ANALYSIS RESULTS:**

- **Existing Related Modules:** [List actual modules found]
- **Current Workflow:** [Describe how similar tasks are currently handled]
- **Integration Decision:** [Extend existing vs create new - with justification]
- **Recommended Entry Point:** [Which existing method/module to modify or where to add new code]

### Existing Technology Stack

- **Python Version:** 3.12+
- **Core Libraries:** sounddevice, evdev, tkinter, pystray, websockets
- **STT Providers:** [Soniox, Deepgram, AssemblyAI, etc.]
- **Processing Pipeline:** Audio Thread -> WebSocket -> Queue -> Injection Thread

### 🚨 INTEGRATION REQUIREMENTS

**Based on your analysis, document:**

- **Files to Modify:** [Specific existing files that need changes]
- **New Files Needed:** [Only if truly necessary]
- **Dependencies to Add:** [Only if existing ones can't handle the task]

---

## 3. 🟡🔴 Strategic Analysis & Solution Options (SKIP for 🟢 Simple Tasks)

### When to Use Strategic Analysis

**✅ CONDUCT STRATEGIC ANALYSIS WHEN:**

- Multiple viable technical approaches exist
- Trade-offs between different solutions are significant
- Change touches multiple threads or hardware inputs
- User has expressed uncertainty about the best approach

### Problem Context

[Explain the problem and why multiple solutions should be considered - what makes this decision important?]

### Solution Options Analysis

#### Option 1: [Solution Name]

**Approach:** [Brief description of this solution approach]

**Pros:**

- ✅ [Advantage 1 - specific benefit]
- ✅ [Advantage 2 - quantified when possible]

**Cons:**

- ❌ [Disadvantage 1 - specific limitation]
- ❌ [Disadvantage 2 - risk or complexity]

**Implementation Complexity:** [Low/Medium/High] - [Brief justification]
**Risk Level:** [Low/Medium/High] - [Primary risk factors]

#### Option 2: [Solution Name]

_(Similar structure to Option 1)_

### Recommendation & Rationale

**🎯 RECOMMENDED SOLUTION:** Option [X] - [Solution Name]
[Why this is the best choice]

### Decision Request

**👤 USER DECISION REQUIRED:**
Based on this analysis, do you want to proceed with the recommended solution (Option [X]), or would you prefer a different approach?

---

## 4. Context & Problem Definition

### When to Use This Section:

✅ **USE:** Always. It provides essential context for the task.
❌ **SKIP:** Never.

### Problem Statement

[Detailed explanation of the problem, including pain points, user impact, and why this needs to be solved now]

### Success Criteria

- [ ] [Specific, measurable outcome 1]
- [ ] [Specific, measurable outcome 2]
- [ ] [Specific, measurable outcome 3]

---

## 5. Development Mode Context

### When to Use This Section:

✅ **USE:** Always. It provides essential guidelines for the project.
❌ **SKIP:** Never.

### Development Mode Context

- **🚨 IMPORTANT: This is a new application in active development**
- **Priority: Speed, Zero latency, and minimal CPU/RAM footprint**
- **Aggressive refactoring allowed** - delete/recreate modules as needed

### 🚨 CRITICAL: Fix Root Problems, Don't Work Around Them

- **If existing code is BROKEN → FIX IT completely**, don't maintain broken contracts
- **If fields/types are WRONG → CHANGE THEM everywhere**
- **When in doubt: Fix the root cause rather than adding workarounds**

---

## 6. 🟡🔴 Technical Requirements (SKIP for 🟢 Simple Config Changes)

### When to Use This Section:

✅ **USE:** New features, module endpoints, performance requirements, security considerations
❌ **SKIP:** Simple bug fixes, configuration updates, adding imports

### Functional Requirements

- [Requirement 1: Module can...]
- [Requirement 2: System will process...]
- [Requirement 3: When X happens, then Y...]

### Non-Functional Requirements

- **Latency:** Max 500ms from speech to injection.
- **Resource Usage:** CPU/RAM footprint must be extremely minimal (Zero bloat).
- **Thread Safety:** Non-blocking UI (Tkinter `.after()`). Ensure thread-safe queue usage.

### Technical Constraints

- [Constraint 1: Must bypass clipboard for English via `evdev` uinput]
- [Constraint 2: Do not freeze the mainloop]

---

## 7. 🟡🔴 State & Persistence (SKIP if no state changes)

### When to Use This Section:

✅ **USE:** Global state changes, thread logic, new JSON history models, RAM management
❌ **SKIP:** No state involvement, configuration-only changes

### Global State Management

- **Threading Flags:** Focus on `threading.Event()` flags used to signal mic activity or API shutdown.
- **Enums & Config:** Use Enums inside `config.py` for cleanly managing active provider states.

### JSON/RAM Logic

- **RAM History:** Maintain a 5-slot RAM history for the last 5 voice-typed sessions.
- **File Persistence:** Handle the `history.json` flush logic on timers and proper app exit hooks (e.g., `atexit` or `pystray` exit).

---

## 8. 🟡🔴 STT Providers & WebSockets (SKIP for internal-only changes)

### When to Use This Section:

✅ **USE:** New APIs, WebSocket integrations, queue producer/consumer changes
❌ **SKIP:** Internal text output changes, configuration updates, simple bug fixes

### WebSocket Lifecycle

- [ ] **Handshakes:** Follow exact documentation for the active STT API.
- [ ] **Audio Chunking:** Push chunked bytes efficiently from the audio thread.
- [ ] **Interim Transcript Filtering:** The backend MUST filter by the `is_final` rule. Discard all "interim" or partial transcripts to prevent duplicate typing glitches.

### Queue Logic

- [ ] **Producer/Consumer:** Ensure text moves cleanly from the WebSocket receiving thread into the `queue.Queue`.
- [ ] **Execution:** The injection thread exclusively reads from the queue for output.

---

## 9. Code Organization & File Structure (SKIP for simple single-file changes)

### When to Use This Section:

✅ **USE:** Multi-file changes, new modules, restructuring package organization
❌ **SKIP:** Single file modifications, configuration changes, simple bug fixes

### New Files to Create

```
voice_typing_app/
│
├── main.py                    # Gateway app.
├── config.py                  # Global settings, keys, and default targets.
├── history.json
├── requirements.txt
│
├── stt/                       # PACKAGE: Streaming Speech-to-Text
│   ├── __init__.py
│   ├── mic.py
│   ├── silence.py
│   └── stt_providers/
│       ├── __init__.py
│       └── base.py
│
├── text_injection/            # PACKAGE: Text Output
│   ├── __init__.py
│   ├── base.py
│   ├── uinput_engine.py
│   └── clipboard_engine.py
│
└── ui/                        # PACKAGE: User Interface
    ├── __init__.py
    ├── tray.py
    └── floating.py
```

### Import Pattern Requirements

**🚨 CRITICAL: Follow these import patterns strictly:**

- **ALWAYS use relative imports** within the same package: `from .models import MyModel`
- **NEVER use absolute imports** for internal modules: ❌ `from text_injection.base import BaseInjector`
- **Enforce Facade Rules:** Add a mandatory check that all new cross-package logic is exposed strictly via the package's `__init__.py`.
- **Use absolute imports ONLY** for external packages: ✅ `import tkinter as tk`

### Dependencies to Add to requirements.txt

**⚠️ CRITICAL: Use pip commands, never uv sync or poetry**

```bash
# Add a new dependency
pip install new-package
pip freeze > requirements.txt
```

---

## 10. Code Quality Standards & Best Practices

### When to Use This Section:

✅ **USE:** Always. These standards must be followed for all code changes.
❌ **SKIP:** Never.

### Python Code Quality Requirements

- [ ] **🚨 FUNCTION INSPECTION:** Always inspect function definitions before calling - never guess parameter types
- [ ] **Type Hints:** Complete type annotations for all functions, classes, and variables
- [ ] **Thread-Safe UI Rule:** Explicitly forbid updating Tkinter widgets from background threads. Use `.after()`.
- [ ] **Context Manager Rule:** Mandate `with evdev.UInput()` and `with sd.InputStream()` to ensure OS hardware is properly released.
- [ ] **IST Logging Requirement:** Include IST (Indian Standard Time) timestamp logic in every new module where logging occurs.
- [ ] **🚨 RELATIVE IMPORTS:** Always use relative imports (`.`) for internal modules
- [ ] **🚨 USE PIP:** Always use `pip` and `requirements.txt` for dependency management.

### Python Code Style & Best Practices

- [ ] **🚨 MANDATORY: Write Professional Comments - Never Historical Comments**
  - **❌ NEVER write change history** or migration artifacts
  - **✅ ALWAYS explain business logic** for future developers
- [ ] **🚨 MANDATORY: Use early returns to keep code clean and readable**
- [ ] **🚨 MANDATORY: NO FALLBACK BEHAVIOR - Always raise exceptions instead**
- [ ] **🚨 MANDATORY: Clean up removal artifacts** completely, no commented dead code

### Validation & Manual Review

All code must be verified manually by the developer and reviewed by the user. No automatic linting tools are used in this project.

### STT Provider Standards

- [ ] **Check documentation:** Verify the specific STT provider's documentation (Soniox, Deepgram, AssemblyAI) directly. Do not assume default REST endpoints.

---

## 11. Implementation Plan

### When to Use This Section:

✅ **USE:** Always. Every task needs a clear plan.
❌ **SKIP:** Never.

### Phase 1: [Phase Name]

**Goal:** [What this phase accomplishes]

- [ ] **Task 1.1:** [Specific task with module paths]
  - Files: `stt/stt_providers/base.py`
  - Details: [Technical specifics and implementation notes]

### Phase 2: [Phase Name]

**Goal:** [What this phase accomplishes]

- [ ] **Task 2.1:** [Integration and hardware endpoints]

### Phase 3: Basic Code Validation (AI-Only)

**Goal:** Run basic automated checks

- [ ] **Task 3.1:** Code Quality Verification
  - Files: All modified files
- [ ] **Task 3.2:** Import and Syntax Validation

### Phase 4: Manual Code Review (Mandatory)

**Goal:** Present "Implementation Complete!" and wait for user manual review

🚨 **CRITICAL WORKFLOW CHECKPOINT:**

- [ ] **Task 4.1:** Present Implementation Complete Message (MANDATORY)
  - **Action:** Present the exact "Implementation Complete!" message and wait for user approval.

- [ ] **Task 4.2:** Final Manual Verification (By User)
  - **Action:** Request the user to manually verify changes match task requirements exactly.

### Task Completion Tracking - MANDATORY WORKFLOW

**🚨 CRITICAL: Real-Time Task Document Updates Are MANDATORY**

- [ ] **🗓️ GET TODAY'S DATE FIRST** - Before adding any completion timestamps, use the `time` or `date` tool to get the correct current date.
- [ ] **🛑 STOP after completing ANY subtask** - Before moving to the next task
- [ ] **📝 IMMEDIATELY open the task document** - Don't wait until the end
- [ ] **✅ Mark checkbox as [x]** with completion timestamp using ACTUAL current date: `✓ 2026-04-03 17:45`
- [ ] **📁 Add file details** with specific paths and changes made

---

## 12. 🔴 Error Handling & Edge Cases (SKIP for simple changes)

### When to Use This Section:

✅ **USE:** Complex hardware interactions, WebSocket/API changes, thread safety
❌ **SKIP:** Simple configuration changes, UI tweaks, non-critical updates

### Error Scenarios

- [ ] **Hardware Errors**
  - **Handling:** Gracefully catch mic disconnects or "Permission denied" for `uinput`.
  - **Resolution:** Re-initialize or prompt the user for fixes without crashing the app.
- [ ] **WebSocket Disconnects**
  - **Handling:** Timeout configuration, automatic WebSocket retry.

### Edge Cases

- [ ] **Tkinter Deadlocks**
  - **Handling:** Ensure pystray runs in a daemon thread and Tkinter mainloop() runs on the Main Thread.
- [ ] **Mixed Method Text**
  - **Solution:** Handling Unicode switching between `evdev` injection and the secure clipboard fallback.

---

## 13. 🔴 Security Considerations (SKIP for internal tools/simple changes)

### When to Use This Section:

✅ **USE:** API key management, OS-level permission changes, udev rules
❌ **SKIP:** Internal logic, configuration tweaks, UI components

### Secret Management

- [ ] All API keys managed strictly via `.env` and `config.py`. Never hardcode secrets.

### OS Permissions

- [ ] Rely on `udev` rules (`input` group membership) for `/dev/uinput` instead of running the entire app with `sudo`.

---

## 14. 🔴 Testing Strategy (OPTIONAL - SKIP unless explicitly requested)

### When to Use This Section:

✅ **USE:** When testing is explicitly requested by the user.
❌ **SKIP:** Default behavior. Focus on what's needed to solve the problem without adding extra testing bloat unless asked.

**📝 NOTE: This section should be SKIPPED unless testing is explicitly required or requested by the user.**

---

## 15. 🔴 Deployment & Configuration (SKIP for development-only changes)

### When to Use This Section:

✅ **USE:** Environment variable changes, external requirements, system configuration
❌ **SKIP:** Development-only features, local testing, standard code updates

### Environment Variables

```bash
# Add these to .env or deployment environment
SONIOX_API_KEY=your-secret-key
DEEPGRAM_API_KEY=your-secret-key
```

---

## 16. 🔴 Second-Order Consequences & Impact Analysis (SKIP for isolated changes)

### When to Use This Section:

✅ **USE:** Architecture changes, breaking changes, cross-thread impacts, system-wide logic
❌ **SKIP:** Bug fixes, configuration changes, isolated module updates

### Impact Assessment Framework

#### 1. **Thread/Hardware Impacts**

- [ ] **Hardware Locking:** Are new hardware instances properly releasing via Context Managers?
- [ ] **Queue Backup:** Will this change block the single FIFO queue used for injection?

#### 2. **Performance Implications**

- [ ] **CPU/RAM Usage:** Will this change introduce heavy polling or RAM bloat?

### Critical Issues Identification

#### 🚨 **RED FLAGS - Alert User Immediately**

These issues must be brought to the user's attention before implementation:

- [ ] **Blocking the Main Thread (Freezing the UI):** Operations that freeze Tkinter loops.
- [ ] **Failing to release Hardware (Zombie Mic):** Omitting context managers on UInput or Mic.
- [ ] **Double Typing Risk:** Modifying STT transcript filtering logic incorrectly (`is_final`).
- [ ] **Data Loss Risk:** Changes that prevent the RAM history from syncing to `history.json`.

---

## 17. AI Agent Instructions

### When to Use This Section:

✅ **USE:** Always. These instructions govern your workflow.
❌ **SKIP:** Never.

### Default Workflow - CODEBASE ANALYSIS FIRST

🎯 **STANDARD OPERATING PROCEDURE:**
When a user requests any new Python feature, improvement, or significant change, your **DEFAULT BEHAVIOR** should be:

1. **CHOOSE COMPLEXITY LEVEL** - Use the triage at the top to determine 🟢🟡🔴
2. **ANALYZE EXISTING CODEBASE** (🟡🔴 only) - Understand current threads, patterns, and workflows FIRST
3. **EVALUATE STRATEGIC NEED** (🟡🔴 only) - Determine if multiple solutions exist or if it's straightforward
4. **STRATEGIC ANALYSIS** (🟡🔴 only) - Present solution options with pros/cons and get user direction
5. **CREATE APPROPRIATELY-SIZED TASK DOCUMENT**
6. **🚨 PRESENT TASK DOCUMENT WITH A/B/C OPTIONS** - Combined approval and implementation choice step
7. **IMPLEMENT THE FEATURE** only after user chooses option B

### Implementation Approach - CRITICAL WORKFLOW

🚨 **MANDATORY: Always follow this exact sequence:**

1. **COMPLEXITY TRIAGE FIRST (Required)**
2. **ANALYZE EXISTING CODEBASE** (🟡🔴 only)
   - [ ] **🚨 INSPECT FUNCTION DEFINITIONS & FACADES**
3. **STRATEGIC ANALYSIS** (🟡🔴 if needed)
4. **CREATE APPROPRIATELY-SIZED TASK DOCUMENT (Required)**
5. **PRESENT TASK DOCUMENT & IMPLEMENTATION OPTIONS (Required)**
   - [ ] **Present the complete task document summary AND implementation options together:**

   ```
   📋 **Task Document Created**

   I've created a [COMPLEXITY LEVEL] task document that proposes [BRIEF SUMMARY OF APPROACH].

   **👤 How would you like to proceed?**

   **A) Preview Detailed Code Changes**
   **B) Approve and Start Implementation**
   **C) Modify the Approach**
   ```

6. **IMPLEMENT PHASE-BY-PHASE (Only after Option B approval)**

   **MANDATORY PHASE WORKFLOW:**
   a. **Execute Phase Completely**
   b. **Update Task Document** - Mark as [x] with exact timestamps
   c. **Provide Specific Phase Recap**

   **🚨 PHASE-SPECIFIC REQUIREMENTS:**
   - [ ] **Real-time task completion tracking**
   - [ ] **Run Python validation** during each phase: compilation, imports
   - [ ] **Use PIP commands exclusively** for dependency management

7. **WORKFLOW CONTINUATION**
   - [ ] **After all implementation phases complete**: Proceed to Phase 4 (Manual Code Review)
   - [ ] **Present "Implementation Complete!" message** and wait for user approval

🛑 **NEVER start coding without explicit A/B/C choice from user!**  
🛑 **NEVER continue to next phase without "proceed" confirmation!**  
🛑 **NEVER skip manual code review after implementation phases!**
🛑 NEVER use uv, multiprocessing, or Any!

### What Constitutes "Explicit User Approval"

#### For Combined Task Document & Implementation Options (Step 5)

**✅ OPTION A RESPONSES (Show detailed code previews):**

- "A" or "Option A"
- "Preview the changes"
- "Show me the code changes"
- "Let me see what will be modified"
- "Walk me through the changes"

**✅ OPTION B RESPONSES (Start implementation immediately):**

- "B" or "Option B"
- "Proceed" or "Go ahead"
- "Approved" or "Start implementation"
- "Begin" or "Execute the plan"
- "Looks good, implement it"

**✅ OPTION C RESPONSES (Provide more feedback):**

- "C" or "Option C"
- "I have questions about..."
- "Can you modify..."
- "What about..." or "How will you handle..."
- "I'd like to change..."
- "Wait, let me think about..."

#### For Phase Continuation

**✅ PHASE CONTINUATION RESPONSES:**

- "proceed"
- "continue"
- "next phase"
- "go ahead"
- "looks good"

**❓ CLARIFICATION NEEDED (Do NOT continue to next phase):**

- Questions about the completed phase
- Requests for changes to completed work
- Concerns about the implementation
- No response or silence

#### For Final Code Review

**✅ CODE REVIEW APPROVAL:**

- "proceed"
- "yes, review the code"
- "go ahead with review"
- "approved"

---

_Template Version: 3.2 - Linux Voice Typing Optimized (Manual Review Only)_  
_Last Updated: 2026-04-06_  
_Refactored for pure Python Thread-based architecture_
