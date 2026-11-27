import threading
import queue
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import fcntl
import signal

import config

# --- SINGLE INSTANCE LOCK ---
LOCK_FILE = "/tmp/voicemint.lock"
_lock_fd = None

def enforce_single_instance():
    global _lock_fd
    # Open with O_RDWR so we can write the PID
    _lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Truncate and write current PID to the lock file
        os.ftruncate(_lock_fd, 0)
        os.write(_lock_fd, str(os.getpid()).encode())
    except BlockingIOError:
        # Read the PID of the existing instance
        try:
            with open(LOCK_FILE, "r") as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    # Send SIGUSR1 to the existing process to wake it up
                    os.kill(pid, signal.SIGUSR1)
        except Exception as e:
            print(f"Failed to signal existing instance: {e}")
            
        print("An instance of VoiceMint is already running.")
        sys.exit(0)

# --- LOGGING SETUP ---
# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure the universal logger
# Requested format: "04 Apr 2026; 02:11:58 PM" -> "%d %b %Y; %I:%M:%S %p"
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
date_format = "%d %b %Y; %I:%M:%S %p"

# Setup root logger with TimedRotatingFileHandler
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Only add the handler if it hasn't been added already to prevent duplicates
if not root_logger.handlers:
    file_handler = TimedRotatingFileHandler(
        filename="logs/voice_typing_logs.log",
        when="midnight",
        interval=1,
        backupCount=config.LOG_KEEP_DAYS,
    )
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance for the given module name.
    """
    return logging.getLogger(name)

# --- GLOBAL STATE FLAGS ---
# The universal kill switch.
# Controls the microphone loop, UI animations, and WebSocket connections.
is_listening = threading.Event()

# Tracks if the WebSocket connection is actively open.
is_connected = threading.Event()

# Global flag to keep the entire application running.
# When cleared, all background threads should finish and the app should exit.
app_running = threading.Event()

# Thread-safe queue for final transcripts.
# STT providers push strings here, the injection engine pulls from here.
transcript_queue: queue.Queue[str] = queue.Queue()

# --- UTILITY FUNCTIONS ---
def paste_last_message() -> None:
    """
    Fetches the last voice-typed message from history, backups the current clipboard,
    copies the message to the clipboard, pastes it, and restores the clipboard.
    """
    import time
    import pyperclip
    import subprocess
    import shutil
    import os
    from history import get_recent_history
    from pynput import keyboard
    from config import CLIPBOARD_RESTORE_DELAY_SEC
    
    logger = get_logger(__name__)
    recent_messages = get_recent_history(limit=1)
    
    if not recent_messages or not recent_messages[0]:
        logger.info("No recent message found in history to paste.")
        return
        
    last_message = recent_messages[0] + " "
    is_wayland = os.environ.get("WAYLAND_DISPLAY") is not None

    def get_primary() -> str:
        try:
            if is_wayland and shutil.which("wl-paste"):
                res = subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True)
                return res.stdout if res.returncode == 0 else ""
            if shutil.which("xclip"):
                res = subprocess.run(["xclip", "-selection", "primary", "-o"], capture_output=True, text=True)
                return res.stdout if res.returncode == 0 else ""
            if shutil.which("xsel"):
                res = subprocess.run(["xsel", "--primary", "--output"], capture_output=True, text=True)
                return res.stdout if res.returncode == 0 else ""
        except: pass
        return ""

    def set_primary(text: str):
        try:
            if is_wayland and shutil.which("wl-copy"):
                subprocess.run(["wl-copy", "--primary"], input=text.encode("utf-8"), check=True)
                return
            if shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "primary"], input=text.encode("utf-8"), check=True)
                return
            if shutil.which("xsel"):
                subprocess.run(["xsel", "--primary", "--input"], input=text.encode("utf-8"), check=True)
                return
        except: pass

    # 1. Backup
    backup_clipboard = ""
    backup_primary = ""
    try:
        backup_clipboard = pyperclip.paste()
        backup_primary = get_primary()
    except Exception as ex:
        logger.warning(f"Could not backup clipboard: {ex}")
        
    # 2. Copy new message
    try:
        pyperclip.copy(last_message)
        set_primary(last_message)
    except Exception as ex:
        logger.warning(f"Could not set clipboard: {ex}")

    time.sleep(0.05)
    
    # 3. Paste via Shift+Insert using pynput
    try:
        controller = keyboard.Controller()
        # Release command/super in case it's still held down
        controller.release(keyboard.Key.cmd)
        
        controller.press(keyboard.Key.shift)
        controller.press(keyboard.Key.insert)
        controller.release(keyboard.Key.insert)
        controller.release(keyboard.Key.shift)
    except Exception as ex:
        logger.error(f"Error simulating paste keys: {ex}")
        
    # 4. Wait for paste to complete
    time.sleep(CLIPBOARD_RESTORE_DELAY_SEC)
    
    # 5. Restore
    try:
        pyperclip.copy(backup_clipboard)
        set_primary(backup_primary)
    except Exception as ex:
        logger.warning(f"Could not restore clipboard: {ex}")
            
    logger.info("Pasted last message and restored clipboard.")

