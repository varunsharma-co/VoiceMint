"""Dictation session: the only behavioral boundary between the terminal and the ports."""

import json
import threading
from typing import Protocol, TextIO

from constants import (
    RECEIVE_TIMEOUT_SECONDS,
    SEND_POLL_TIMEOUT_SECONDS,
    soniox_config,
)
from printer import TranscriptPrinter
from soniox import TokenAssembler


class AudioSource(Protocol):
    def open(self) -> str:
        """Open the input and return the device name."""

    def read(self, timeout: float) -> bytes | None:
        """Return the next PCM block, or None when the wait expires."""

    def close(self) -> None:
        """Release the input. Must be safe to call more than once."""


class ByteSocket(Protocol):
    def connect(self) -> None:
        """Open the transport."""

    def send_text(self, text: str) -> None:
        """Send one text frame."""

    def send_bytes(self, data: bytes) -> None:
        """Send one binary frame."""

    def receive_text(self, timeout: float) -> str | None:
        """Return the next text frame, or None on timeout."""

    def close(self) -> None:
        """Close the transport. Must be safe to call more than once."""


class DictationSession:
    """Stream the audio port to the socket port and write the live transcript."""

    def __init__(
        self,
        api_key: str,
        audio: AudioSource,
        socket: ByteSocket,
        writer: TextIO,
    ) -> None:
        self._api_key = api_key
        self._audio = audio
        self._socket = socket
        self._printer = TranscriptPrinter(writer)
        self._assembler = TokenAssembler()
        self._stop = threading.Event()

    def run(self) -> int:
        """Connect, send the Soniox config, then open the microphone on this thread.

        Returns 0 after Ctrl+C. The caller runs this on the main thread.
        """
        sender: threading.Thread | None = None
        try:
            self._socket.connect()
            self._socket.send_text(json.dumps(soniox_config(self._api_key)))
            device_name = self._audio.open()
            self._printer.listening(device_name)
            sender = threading.Thread(
                target=self._send_audio,
                name="voicemint-audio",
                daemon=True,
            )
            sender.start()
            while not self._stop.is_set():
                incoming = self._socket.receive_text(RECEIVE_TIMEOUT_SECONDS)
                if incoming:
                    self._on_message(incoming)
        except KeyboardInterrupt:
            self._printer.end_partial_line()
            return 0
        finally:
            self._shutdown(sender)
        return 0

    def _on_message(self, raw: str) -> None:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return
        update = self._assembler.apply(payload)
        if update is None:
            return
        text, is_final = update
        if is_final:
            self._printer.final_utterance(text)
        else:
            self._printer.partial_line(text)

    def _send_audio(self) -> None:
        while not self._stop.is_set():
            chunk = self._audio.read(SEND_POLL_TIMEOUT_SECONDS)
            if not chunk:
                continue
            try:
                self._socket.send_bytes(chunk)
            except Exception:
                if self._stop.is_set():
                    return
                raise

    def _shutdown(self, sender: threading.Thread | None) -> None:
        self._stop.set()
        self._audio.close()
        if sender is not None:
            sender.join(timeout=1.5)
        self._socket.close()
