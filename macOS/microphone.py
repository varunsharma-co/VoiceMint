"""Default-input port. Captures 16 kHz mono 16-bit PCM and nothing else."""

import queue
import threading

import sounddevice as sd

from constants import CHANNELS, FRAMES_PER_BLOCK, SAMPLE_RATE


class DefaultMicrophone:
    """System default input. Open it on the main thread so macOS can show the permission dialog."""

    def __init__(self) -> None:
        self._chunks: queue.Queue[bytes] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._running = False
        self._closed = False

    def open(self) -> str:
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("The default microphone must be opened on the main thread.")

        self._closed = False
        self._running = True
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=FRAMES_PER_BLOCK,
            callback=self._on_audio,
        )
        self._stream = stream
        try:
            stream.start()
        except Exception:
            self.close()
            raise

        info = sd.query_devices(stream.device)
        return str(info["name"])

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
        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def _on_audio(self, indata, _frames, _time_info, _status) -> None:
        # Native int16 on Apple Silicon is already little-endian pcm_s16le.
        # tobytes() copies the block; PortAudio reuses the buffer after return.
        if self._running:
            self._chunks.put(indata.tobytes())
