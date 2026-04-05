from abc import ABC, abstractmethod
from typing import Callable

# The callback signature provided by the orchestrator to process received text
TranscriptCallback = Callable[[str, bool], None]

class BaseTranscriber(ABC):
    """
    Abstract Base Class for a real-time streaming transcriber.
    It defines the decoupled interface where the STT client handles networking
    while external code (mic.py) manages the hardware audio capture.
    """

    def __init__(self, api_key: str, callback: TranscriptCallback):
        self.api_key = api_key
        self.callback = callback

    @abstractmethod
    def start_connection(self, sample_rate: int) -> None:
        """
        Initializes the WebSocket/network connection to the remote STT service.
        Must be called before streaming audio chunks.
        """
        pass

    @abstractmethod
    def send_audio_chunk(self, audio_chunk: bytes) -> None:
        """
        Streams a chunk of raw PCM audio bytes to the remote provider.
        """
        pass

    @abstractmethod
    def close_connection(self) -> None:
        """
        Cleanly closes the network connection and terminates any background message handlers.
        """
        pass
