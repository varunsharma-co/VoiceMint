import os
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

# --- SECRETS & API KEYS ---
_SONIOX_API_KEY = os.getenv("SONIOX_API_KEY")
_DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
_ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

STT_API_KEYS = {
    STTProvider.SONIOX: _SONIOX_API_KEY,
    STTProvider.DEEPGRAM: _DEEPGRAM_API_KEY,
    STTProvider.ASSEMBLYAI: _ASSEMBLYAI_API_KEY,
}
