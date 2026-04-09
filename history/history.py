import json
import os
import threading
import time
import atexit
from typing import List

import config
from config import MAX_HISTORY_MESSAGES
from utils import get_logger

logger = get_logger(__name__)

# Ensure the file is saved in the same directory as this script (the history/ folder)
HISTORY_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")

_pending_sessions: List[str] = []
_lock = threading.Lock()

def add_session(text: str) -> None:
    """Adds a finalized session text to the pending memory buffer and truncates to MAX_HISTORY_MESSAGES."""
    text = text.strip()
    if not text:
        return
        
    with _lock:
        _pending_sessions.append(text)
        # Keep only the last N messages in RAM to match the disk limit
        if len(_pending_sessions) > MAX_HISTORY_MESSAGES:
            del _pending_sessions[:-MAX_HISTORY_MESSAGES]
            
    logger.info(f"Session added to memory buffer. Pending sessions: {len(_pending_sessions)}")

def flush_history() -> None:
    """
    Flushes the pending sessions buffer to history.json.
    Reads the existing file, appends new sessions, truncates to MAX_HISTORY_MESSAGES,
    and writes back to disk safely.
    """
    with _lock:
        if not _pending_sessions:
            return
            
        sessions_to_write = list(_pending_sessions)
        _pending_sessions.clear()

    logger.info(f"Flushing {len(sessions_to_write)} sessions to {HISTORY_FILE}...")
    
    # 1. Read existing history
    existing_history: List[str] = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_history = data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read existing {HISTORY_FILE}, starting fresh. Error: {e}")
            existing_history = []
            
    # 2. Append and truncate
    existing_history.extend(sessions_to_write)
    if len(existing_history) > MAX_HISTORY_MESSAGES:
        existing_history = existing_history[-MAX_HISTORY_MESSAGES:]
        
    # 3. Write back
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_history, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {HISTORY_FILE} (total messages: {len(existing_history)})")
    except OSError as e:
        logger.error(f"Failed to write to {HISTORY_FILE}: {e}")

def _history_timer_loop() -> None:
    """A background daemon loop that flushes history every N minutes."""
    while True:
        time.sleep(config.HISTORY_SAVE_INTERVAL_MINUTES * 60)
        flush_history()

def start_background_timer() -> None:
    """Spawns the background daemon thread to manage history flushing."""
    timer_thread = threading.Thread(target=_history_timer_loop, daemon=True)
    timer_thread.start()
    logger.info(f"History background timer started ({config.HISTORY_SAVE_INTERVAL_MINUTES} min interval).")

def get_recent_history(limit: int = 3) -> List[str]:
    """Retrieves the most recent history messages, combining disk and memory buffer."""
    history_list: List[str] = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    history_list = data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read existing {HISTORY_FILE}: {e}")
            
    with _lock:
        history_list.extend(_pending_sessions)
        
    return history_list[-limit:] if history_list else []

# Register the hard flush hook to run on program exit/crash
atexit.register(flush_history)
