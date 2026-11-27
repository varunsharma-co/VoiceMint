"""Capture format and the Soniox session values shared with the Linux client."""

SAMPLE_RATE = 16_000
CHANNELS = 1
BLOCK_DURATION_SECONDS = 0.1
FRAMES_PER_BLOCK = int(SAMPLE_RATE * BLOCK_DURATION_SECONDS)

SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"
SONIOX_MODEL = "stt-rt-v5"
LANGUAGE_HINTS = ("en",)
MAX_ENDPOINT_DELAY_MS = 1000
AUDIO_FORMAT = "pcm_s16le"
PING_INTERVAL_SECONDS = 20
PING_TIMEOUT_SECONDS = 30
RECEIVE_TIMEOUT_SECONDS = 1.0
SEND_POLL_TIMEOUT_SECONDS = 0.1


def soniox_config(api_key: str) -> dict:
    """JSON object for the first Soniox frame. No other fields belong here."""
    return {
        "api_key": api_key,
        "model": SONIOX_MODEL,
        "language_hints": list(LANGUAGE_HINTS),
        "language_hints_strict": True,
        "enable_language_identification": False,
        "enable_speaker_diarization": False,
        "enable_endpoint_detection": True,
        "max_endpoint_delay_ms": MAX_ENDPOINT_DELAY_MS,
        "audio_format": AUDIO_FORMAT,
        "sample_rate": SAMPLE_RATE,
        "num_channels": CHANNELS,
    }
