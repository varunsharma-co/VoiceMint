import json
import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class STTProvider(Enum):
    """Enumeration of supported real-time Speech-to-Text APIs."""

    SONIOX = "soniox"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"


class LLMProvider(Enum):
    """Enumeration of supported LLM API providers."""

    GEMINI_FLASH_2_5_LITE = "gemini_flash_2_5_lite"


class InjectionMethod(Enum):
    """Enumeration of supported text injection methods."""

    UINPUT = "uinput"
    CLIPBOARD = "clipboard"


# --- JSON CONFIGURATION LOADER ---
CONFIG_PATH = Path(__file__).parent / "config.json"

_DEFAULT_CONFIG = {
    "ACTIVE_STT_PROVIDER": "soniox",
    "ACTIVE_INJECTION_METHOD": "uinput",
    "SILENCE_TIMEOUT_SECONDS": 45.0,
    "SAMPLE_RATE": 16000,
    "HOTKEY_START": "<cmd>+u",
    "HOTKEY_STOP": "<cmd>+i",
    "HOTKEY_COPY_LAST": "<cmd>+h",
    "MAX_HISTORY_MESSAGES": 5,
    "HISTORY_SAVE_INTERVAL_MINUTES": 60.0,
    "IDEAL_FLUSH_WORD_COUNT": 8,
    "FAILSAFE_FLUSH_MULTIPLIER": 1.6,
    "CLIPBOARD_RESTORE_DELAY_SEC": 0.5,
    "LOG_KEEP_DAYS": 7,
    "DEFAULT_LLM_PROVIDER": "gemini_flash_2_5_lite",
}

def _load_config() -> dict:
    config_data = _DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                user_config = json.load(f)
                config_data.update(user_config)
        except Exception as e:
            print(f"Error loading config.json: {e}")
    else:
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error writing default config.json: {e}")
    return config_data

_current_config = _load_config()

# --- APPLICATION SETTINGS ---
try:
    ACTIVE_STT_PROVIDER = STTProvider(_current_config["ACTIVE_STT_PROVIDER"])
except ValueError:
    ACTIVE_STT_PROVIDER = STTProvider.SONIOX

try:
    ACTIVE_INJECTION_METHOD = InjectionMethod(_current_config["ACTIVE_INJECTION_METHOD"])
except ValueError:
    ACTIVE_INJECTION_METHOD = InjectionMethod.UINPUT

try:
    DEFAULT_LLM_PROVIDER = LLMProvider(_current_config["DEFAULT_LLM_PROVIDER"])
except (ValueError, KeyError):
    DEFAULT_LLM_PROVIDER = LLMProvider.GEMINI_FLASH_2_5_LITE

SILENCE_TIMEOUT_SECONDS = float(_current_config["SILENCE_TIMEOUT_SECONDS"])
SAMPLE_RATE = int(_current_config["SAMPLE_RATE"])

# --- HOTKEY SETTINGS ---
HOTKEY_START = str(_current_config["HOTKEY_START"])
HOTKEY_STOP = str(_current_config["HOTKEY_STOP"])
HOTKEY_COPY_LAST = str(_current_config.get("HOTKEY_COPY_LAST", "<cmd>+h"))

# --- SESSION HISTORY SETTINGS ---
MAX_HISTORY_MESSAGES = int(_current_config["MAX_HISTORY_MESSAGES"])
HISTORY_SAVE_INTERVAL_MINUTES = float(_current_config["HISTORY_SAVE_INTERVAL_MINUTES"])

# --- CLIPBOARD INJECTION TUNING ---
IDEAL_FLUSH_WORD_COUNT = int(_current_config["IDEAL_FLUSH_WORD_COUNT"])
FAILSAFE_FLUSH_MULTIPLIER = float(_current_config["FAILSAFE_FLUSH_MULTIPLIER"])
CLIPBOARD_RESTORE_DELAY_SEC = float(_current_config["CLIPBOARD_RESTORE_DELAY_SEC"])

# --- LOGGING SETTINGS ---
LOG_KEEP_DAYS = int(_current_config.get("LOG_KEEP_DAYS", 7))

# =====================================================================
# SPEECH_ENDPOINT_DELAY_MS
# The pause duration (in milliseconds) the Speech-to-Text server waits
# after you stop speaking before deciding you have finished a sentence
# and finalizing the text injection.
# Range: 500 ms to 3000 ms.
# =====================================================================
SPEECH_ENDPOINT_DELAY_MS = 1000

# --- SECRETS & API KEYS ---
_SONIOX_API_KEY = os.getenv("SONIOX_API_KEY")
_DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
_ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

STT_API_KEYS = {
    STTProvider.SONIOX: _SONIOX_API_KEY,
    STTProvider.DEEPGRAM: _DEEPGRAM_API_KEY,
    STTProvider.ASSEMBLYAI: _ASSEMBLYAI_API_KEY,
}
