## Problem

The application log file `logs/voice_typing_logs.log` grows indefinitely over time, leading to potential disk space issues and making log analysis difficult.

## Solution

Replace the static `logging.basicConfig` with a `TimedRotatingFileHandler`. This handler will be configured to automatically rotate logs daily at midnight and preserve a defined number of backups. The retention duration will be controlled by a new `LOG_KEEP_DAYS` setting in `config.json` (defaulting to 7).

## Implementation

- [x] ✓ 2026-04-09 13:43 **Task 1:** Update Configuration Management
  - Files: `config.json`, `config.py`
  - Details: Add `"LOG_KEEP_DAYS": 7` to `config.json` and the default dictionary in `config.py`. Expose it as an integer variable `LOG_KEEP_DAYS` in `config.py`.
- [x] ✓ 2026-04-09 13:43 **Task 2:** Refactor Logging Setup
  - Files: `utils.py`
  - Details: Import `TimedRotatingFileHandler` from `logging.handlers`. Replace `logging.basicConfig` with a root logger setup or module-level handler. Set `when="midnight"` and `backupCount=LOG_KEEP_DAYS` (loaded from `config.py`). Apply the existing `log_format` and `date_format` using `logging.Formatter`. Ensure handlers are only attached once to prevent duplicate log entries when `get_logger()` is called.

## Files to Modify

- `config.json` - Add default variable.
- `config.py` - Load variable.
- `utils.py` - Setup rotating file handler and prevent handler duplication.

**Time Estimate:** 15 minutes
