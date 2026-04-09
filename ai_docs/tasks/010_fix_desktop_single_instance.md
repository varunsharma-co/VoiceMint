## Problem

When a second instance of VoiceMint is launched via the desktop icon (`Terminal=false`), the app silently fails to acquire the instance lock and exits without any visual feedback, as the terminal output is hidden. The user thinks the app failed to launch, while the existing instance is not brought to the foreground.

## Solution

Modify the single-instance enforcement logic to save the active PID in the lock file. When a second instance hits the lock, it will read the PID and send a POSIX signal (`SIGUSR1`) to the first instance. The original instance will catch this signal and automatically restore its window to the foreground.

## Implementation

- [x] **Task 1:** Update lock logic to write PID and signal existing instance ✓ 2026-04-09 15:21
  - Files: `main.py`
  - Details: Import `signal`. Update `enforce_single_instance()` to truncate the lock file and write `os.getpid()` to it. In the `BlockingIOError` block, read the PID from the lock file and use `os.kill(pid, signal.SIGUSR1)` to signal the existing instance before exiting.
- [x] **Task 2:** Add signal handler to restore UI and show dialog ✓ 2026-04-09 15:23
  - Files: `ui/floating.py`
  - Details: Import `signal` and `tkinter.messagebox`. In `VoiceMintUI.__init__`, add `signal.signal(signal.SIGUSR1, self._handle_sigusr1)`. Create `_handle_sigusr1(self, signum, frame)` which calls `self._restore_from_tray()` and then shows an info messagebox saying "VoiceMint is already running.".

## Files to Modify

- `main.py` - Update `enforce_single_instance()` with PID writing and signaling.
- `ui/floating.py` - Add signal listener and UI restore handler.

**Time Estimate:** 15-30 minutes