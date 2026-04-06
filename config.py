import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class STTProvider(Enum):
    """Enumeration of supported real-time Speech-to-Text APIs."""

    SONIOX = "soniox"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"


class InjectionMethod(Enum):
    """Enumeration of supported text injection methods."""

    UINPUT = "uinput"
    CLIPBOARD = "clipboard"


# --- APPLICATION SETTINGS ---
ACTIVE_STT_PROVIDER = STTProvider.SONIOX
ACTIVE_INJECTION_METHOD = InjectionMethod.CLIPBOARD
SILENCE_TIMEOUT_SECONDS = 45.0
SAMPLE_RATE = 16000

# --- SESSION HISTORY SETTINGS ---
MAX_HISTORY_MESSAGES = 5
HISTORY_SAVE_INTERVAL_MINUTES = 60.0

# --- CLIPBOARD INJECTION TUNING ---
IDEAL_FLUSH_WORD_COUNT = 10
FAILSAFE_FLUSH_MULTIPLIER = 1.6
CLIPBOARD_RESTORE_DELAY_SEC = 0.5

# --- SECRETS & API KEYS ---
_SONIOX_API_KEY = os.getenv("SONIOX_API_KEY")
_DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
_ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

STT_API_KEYS = {
    STTProvider.SONIOX: _SONIOX_API_KEY,
    STTProvider.DEEPGRAM: _DEEPGRAM_API_KEY,
    STTProvider.ASSEMBLYAI: _ASSEMBLYAI_API_KEY,
}
