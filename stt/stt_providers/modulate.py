import json
import threading
from typing import Optional
from urllib.parse import urlencode

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect, ClientConnection

import utils
import config
from .base import BaseTranscriber, TranscriptCallback

# Base WebSocket URL for Modulate English Fast streaming transcription
MODULATE_WS_BASE_URL = "wss://platform.modulate.ai/api/velma-2-stt-streaming-english-v2"


class ModulateTranscriber(BaseTranscriber):
    """
    Implementation of the real-time transcriber for the Modulate English Fast service.
    Decoupled from audio capture; relies on mic.py to send audio chunks.
    """

    def __init__(self, api_key: str, callback: TranscriptCallback):
        super().__init__(api_key, callback)
        self._stop_event = threading.Event()
        self.ws: Optional[ClientConnection] = None
        self.message_thread: Optional[threading.Thread] = None
        self._connection_closed = True

    def _message_handler(self) -> None:
        """Handles incoming messages from the WebSocket server."""
        if not self.ws:
            return

        try:
            # Aggressively check stop event and global app_running flag
            while not self._stop_event.is_set() and utils.app_running.is_set():
                try:
                    message = self.ws.recv(timeout=1.0)
                except TimeoutError:
                    continue  # Check stop event again

                res = json.loads(message)
                msg_type = res.get("type")

                if msg_type == "error":
                    print(f"[STT Provider: Modulate] Error: {res.get('error')}")
                    break
                elif msg_type == "partial_utterance":
                    partial = res.get("partial_utterance", {})
                    transcript = partial.get("text", "")
                    if transcript:
                        self.callback(transcript, False)
                elif msg_type == "utterance":
                    utterance = res.get("utterance", {})
                    transcript = utterance.get("text", "")
                    if transcript:
                        self.callback(transcript, True)
                elif msg_type == "done":
                    print("[STT Provider: Modulate] Session completed.")
                    break

        except ConnectionClosed:
            if not self._connection_closed:
                print("[STT Provider: Modulate] WebSocket connection closed by server.")
        except Exception as e:
            if utils.app_running.is_set() and not self._connection_closed:
                print(f"[STT Provider: Modulate] Message handler error: {e}")
        finally:
            self._stop_event.set()

    def start_connection(self, sample_rate: int) -> None:
        """
        Initializes the WebSocket connection to Modulate and starts the message loop.
        """
        self._stop_event.clear()
        self._connection_closed = False

        params = {
            "api_key": self.api_key,
            "audio_format": "s16le",
            "sample_rate": sample_rate,
            "num_channels": 1,
            "endpointing": "true",
        }
        url = f"{MODULATE_WS_BASE_URL}?{urlencode(params)}"

        try:
            self.ws = connect(
                url,
                ping_interval=config.WEBSOCKET_PING_INTERVAL,
                ping_timeout=config.WEBSOCKET_PING_TIMEOUT,
            )
            print("[STT Provider: Modulate] Connected via WebSocket.")

            # Start background thread to listen for server responses
            self.message_thread = threading.Thread(target=self._message_handler, daemon=True)
            self.message_thread.start()
        except Exception as e:
            print(f"[STT Provider: Modulate] Failed to connect: {e}")
            self.close_connection()
            raise

    def send_audio_chunk(self, audio_chunk: bytes) -> None:
        """
        Sends raw PCM audio bytes to the connected WebSocket.
        """
        if self.ws and not self._stop_event.is_set() and utils.app_running.is_set() and not self._connection_closed:
            try:
                self.ws.send(audio_chunk)
            except Exception as e:
                if utils.app_running.is_set() and not self._connection_closed:
                    print(f"[STT Provider: Modulate] Failed to send audio chunk: {e}")
                self._stop_event.set()

    def close_connection(self) -> None:
        """
        Closes the WebSocket connection and waits for the message thread to exit.
        Idempotent: Only runs teardown once.
        """
        if self._connection_closed:
            return

        self._connection_closed = True
        self._stop_event.set()

        if self.ws:
            try:
                # Send empty text frame to signal end of stream to Modulate server
                self.ws.send("")
            except Exception:
                pass

            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=1.5)

        print("[STT Provider: Modulate] Disconnected and cleaned up resources.")
