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

# Global flag to keep the entire application running.
# When cleared, all background threads should finish and the app should exit.
app_running = threading.Event()

# Thread-safe queue for final transcripts.
# STT providers push strings here, the injection engine pulls from here.
transcript_queue: queue.Queue[str] = queue.Queue()

