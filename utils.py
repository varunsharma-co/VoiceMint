import threading
import queue
import logging
import os

# --- LOGGING SETUP ---
# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure the universal logger
# Requested format: "04 Apr 2026; 02:11:58 PM" -> "%d %b %Y; %I:%M:%S %p"
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
date_format = "%d %b %Y; %I:%M:%S %p"

logging.basicConfig(
    filename="logs/voice_typing_logs.log",
    level=logging.INFO,
    format=log_format,
    datefmt=date_format,
)

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

