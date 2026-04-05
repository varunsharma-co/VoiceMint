import os
import queue
import threading
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

class STTProvider(Enum):
    """Enumeration of supported real-time Speech-to-Text APIs."""
    SONIOX = "soniox"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"

# --- APPLICATION SETTINGS ---
ACTIVE_STT_PROVIDER = STTProvider.SONIOX
SILENCE_TIMEOUT_SECONDS = 45.0
SAMPLE_RATE = 16000

# --- GLOBAL STATE FLAGS ---
# The universal kill switch. Controls the microphone loop, UI animations, and WebSocket connections.
is_listening = threading.Event()

# Thread-safe queue for final transcripts. 
# STT providers push strings here, the injection engine pulls from here.
transcript_queue: queue.Queue[str] = queue.Queue()

# --- SECRETS & API KEYS ---
_SONIOX_API_KEY = os.getenv("SONIOX_API_KEY")
_DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
_ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

STT_API_KEYS = {
    STTProvider.SONIOX: _SONIOX_API_KEY,
    STTProvider.DEEPGRAM: _DEEPGRAM_API_KEY,
    STTProvider.ASSEMBLYAI: _ASSEMBLYAI_API_KEY,
}
