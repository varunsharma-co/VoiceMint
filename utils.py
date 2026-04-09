import threading
import queue
import logging
from logging.handlers import TimedRotatingFileHandler
import os

import config

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

