"""Dictation session: the only behavioral boundary between the terminal and the ports."""

import json
import sys
import threading
from typing import Protocol, TextIO

from constants import (
    RECEIVE_TIMEOUT_SECONDS,
    SEND_POLL_TIMEOUT_SECONDS,
    soniox_config,
)
from printer import TranscriptPrinter
from soniox import TokenAssembler


def _one_line(value: object) -> str:
    """Flatten a provider or socket error so the transcript gets one line."""
    return " ".join(str(value).split())


class MicrophoneOpenError(Exception):
    """The default input rejected the capture format."""

    def __init__(self, device_name: str, portaudio_error: str) -> None:
        self.device_name = device_name
        self.portaudio_error = portaudio_error
        super().__init__(f"{device_name}: {portaudio_error}")


class AudioSource(Protocol):
    def open(self) -> str:
        """Open the input and return the device name.

        Raise `MicrophoneOpenError` when the device rejects the capture format.
        `device_name` and `portaudio_error` are the two facts the session prints.
        """

    def read(self, timeout: float) -> bytes | None:
        """Return the next PCM block, or None when the wait expires."""

    def take_warning(self) -> str | None:
        """Return one pending PortAudio status warning, or None."""

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
        self._send_failed = threading.Event()
        self._send_error: BaseException | None = None

    def run(self) -> int:
        """Connect, send the Soniox config, then open the microphone on this thread.

        Returns 0 when the user stops the session or Soniox finishes it, and 1
        when setup or the connection fails. The caller runs this on the main thread.
        """
        if self._api_key.strip() == "":
            self._printer.error("SONIOX_API_KEY is missing.")
            return 1

        sender: threading.Thread | None = None
        try:
            try:
                self._socket.connect()
                self._socket.send_text(json.dumps(soniox_config(self._api_key)))
            except Exception as exc:
                self._printer.error(f"Could not reach Soniox: {_one_line(exc)}")
                return 1

            try:
                device_name = self._audio.open()
            except MicrophoneOpenError as exc:
                self._printer.error(
                    f"Could not open {exc.device_name}: {_one_line(exc.portaudio_error)}"
                )
                return 1

            self._printer.listening(device_name)
            sender = threading.Thread(
                target=self._send_audio,
                name="voicemint-audio",
                daemon=True,
            )
            sender.start()
            while not self._stop.is_set():
                send_exit = self._send_failure_exit_code()
                if send_exit is not None:
                    return send_exit
                self._report_audio_warnings()
                try:
                    incoming = self._socket.receive_text(RECEIVE_TIMEOUT_SECONDS)
                except Exception as exc:
                    send_exit = self._send_failure_exit_code()
                    if send_exit is not None:
                        return send_exit
                    self._printer.error(f"Soniox connection closed: {_one_line(exc)}")
                    return 1
                if not incoming:
                    continue
                outcome = self._on_message(incoming)
                if outcome is not None:
                    return outcome
        except KeyboardInterrupt:
            send_exit = self._send_failure_exit_code()
            if send_exit is not None:
                return send_exit
            self._printer.end_partial_line()
            return 0
        finally:
            self._shutdown(sender)
        return 0

    def _on_message(self, raw: str) -> int | None:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return None
        error_code = payload.get("error_code")
        if error_code:
            message = payload.get("error_message", "")
            self._printer.error(f"Soniox error {error_code}: {_one_line(message)}")
            return 1
        update = self._assembler.apply(payload)
        if update is not None:
            text, is_final = update
            if is_final:
                self._printer.final_utterance(text)
            else:
                self._printer.partial_line(text)
        if payload.get("finished"):
            self._printer.end_partial_line()
            return 0
        return None

    def _send_audio(self) -> None:
        while not self._stop.is_set():
            chunk = self._audio.read(SEND_POLL_TIMEOUT_SECONDS)
            if not chunk:
                continue
            try:
                self._socket.send_bytes(chunk)
            except Exception as exc:
                # A close this session already started can fail the in-flight send.
                if self._stop.is_set():
                    return
                self._send_error = exc
                self._send_failed.set()
                return

    def _report_audio_warnings(self) -> None:
        """Print each pending status warning and put the open transcript line back."""
        while True:
            raw = self._audio.take_warning()
            if not raw:
                return
            warning = _one_line(raw)
            if not warning:
                continue
            # Clear to the end of the line. A short warning must not leave the
            # tail of a longer partial in the scrollback when stderr shares the cursor.
            sys.stderr.write(f"\r{warning}\x1b[K\n")
            sys.stderr.flush()
            self._printer.redraw()

    def _send_failure_exit_code(self) -> int | None:
        """1 after printing the upload error, or None while the upload is healthy."""
        if not self._send_failed.is_set():
            return None
        detail = _one_line(self._send_error) if self._send_error is not None else ""
        self._printer.error(f"Could not send audio to Soniox: {detail}")
        return 1

    def _shutdown(self, sender: threading.Thread | None) -> None:
        # Stop before closing. The close unblocks an in-flight send, and that
        # send then fails. `run` has already chosen its exit code; an exception
        # from `close` would discard that return.
        self._stop.set()
        _close_quietly(self._audio)
        _close_quietly(self._socket)
        if sender is not None:
            sender.join(timeout=1.5)


def _close_quietly(port: AudioSource | ByteSocket) -> None:
    try:
        port.close()
    except Exception:
        pass
