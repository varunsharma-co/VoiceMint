"""Default-input port. Captures 16 kHz mono 16-bit PCM and nothing else."""

import queue
import threading

import sounddevice as sd

from constants import CHANNELS, FRAMES_PER_BLOCK, SAMPLE_RATE
from session import MicrophoneOpenError


def _one_line(value: object) -> str:
    return " ".join(str(value).split())


class DefaultMicrophone:
    """System default input. Open it on the main thread so macOS can show the permission dialog."""

    def __init__(self) -> None:
        # Unbounded: a brief send stall must not drop blocks already captured.
        self._chunks: queue.Queue[bytes] = queue.Queue()
        self._warnings: queue.Queue[str] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._running = False
        self._closed = False

    def open(self) -> str:
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("The default microphone must be opened on the main thread.")

        self._closed = False
        self._running = True
        self._discard_pending()
        device_name = "default input"
        try:
            device_name = _default_input_name()
            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=FRAMES_PER_BLOCK,
                callback=self._on_audio,
            )
            self._stream = stream
            stream.start()
            opened_name = str(sd.query_devices(stream.device)["name"])
        except Exception as exc:
            self.close()
            raise MicrophoneOpenError(device_name, _one_line(exc)) from exc
        return opened_name

    def take_warning(self) -> str | None:
        try:
            return self._warnings.get_nowait()
        except queue.Empty:
            return None

    def _discard_pending(self) -> None:
        while True:
            try:
                self._chunks.get_nowait()
            except queue.Empty:
                break
        while True:
            try:
                self._warnings.get_nowait()
            except queue.Empty:
                return

    def read(self, timeout: float) -> bytes | None:
        try:
            return self._chunks.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._running = False
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        # Abort releases the device immediately so a later run can open it.
        # stop() would wait out the current input buffer first.
        try:
            stream.abort()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def _on_audio(self, indata, _frames, _time_info, status) -> None:
        # Native int16 on Apple Silicon is already little-endian pcm_s16le.
        # tobytes() copies the block; PortAudio reuses the buffer after return.
        if not self._running:
            return
        if status:
            warning = " ".join(str(status).split())
            if warning:
                self._warnings.put(warning)
        self._chunks.put(indata.tobytes())


def _default_input_name() -> str:
    info = sd.query_devices(kind="input")
    name = info["name"] if isinstance(info, dict) else ""
    if isinstance(name, str) and name.strip():
        return name
    return "default input"
