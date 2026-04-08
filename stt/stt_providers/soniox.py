import json
import threading
from typing import List, Optional

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect, ClientConnection

import utils
from .base import BaseTranscriber, TranscriptCallback

SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"

class SonioxTranscriber(BaseTranscriber):
    """
    Implementation of the real-time transcriber for the Soniox service.
    Decoupled from audio capture; relies on mic.py to send audio chunks.
    """

    def __init__(self, api_key: str, callback: TranscriptCallback):
        super().__init__(api_key, callback)
        self.final_tokens: List[str] = []
        self._stop_event = threading.Event()
        self.ws: Optional[ClientConnection] = None
        self.message_thread: Optional[threading.Thread] = None
        self._connection_closed = True  # Start in closed state

    def _get_config(self, sample_rate: int) -> dict:
        """Builds the configuration JSON for the Soniox API."""
        return {
            "api_key": self.api_key,
            "model": "stt-rt-v4",
            "language_hints": ["en"],
            "enable_language_identification": False,
            "enable_speaker_diarization": False,
            "enable_endpoint_detection": True,
            "audio_format": "pcm_s16le",
            "sample_rate": sample_rate,
            "num_channels": 1,
            "language_hints_strict": True,
        }

    def _render_transcript(self, non_final_tokens: List[dict]) -> str:
        """Combines final and non-final tokens into a single string."""
        interim_transcript = "".join(token.get("text", "") for token in non_final_tokens)
        full_transcript = "".join(self.final_tokens) + interim_transcript
        return full_transcript

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

                if res.get("error_code"):
                    print(f"[STT Provider: Soniox] Error: {res['error_code']} - {res['error_message']}")
                    break

                non_final_tokens = []
                new_final_count = 0

                for token in res.get("tokens", []):
                    token_text = token.get("text")

                    # The Soniox API sends a literal "<end>" token when endpointing is enabled.
                    # Explicitly ignore this token.
                    if not token_text or token_text == "<end>":
                        continue

                    if token.get("is_final"):
                        self.final_tokens.append(token_text)
                        new_final_count += 1
                    else:
                        non_final_tokens.append(token)

                full_transcript = self._render_transcript(non_final_tokens)
                is_final_update = new_final_count > 0 and not non_final_tokens

                if full_transcript or is_final_update:
                    self.callback(full_transcript, is_final_update)

                if is_final_update:
                    self.final_tokens = []

                if res.get("finished"):
                    print("[STT Provider: Soniox] Session finished.")
                    break
                    
        except ConnectionClosed:
            # Only print if we haven't already explicitly closed the connection
            if not self._connection_closed:
                print("[STT Provider: Soniox] WebSocket connection closed by server.")
        except Exception as e:
            if utils.app_running.is_set() and not self._connection_closed:
                print(f"[STT Provider: Soniox] Message handler error: {e}")
        finally:
            self._stop_event.set()

    def start_connection(self, sample_rate: int) -> None:
        """
        Initializes the WebSocket connection to Soniox and starts the message loop.
        """
        self._stop_event.clear()
        self.final_tokens = []
        self._connection_closed = False
        
        try:
            self.ws = connect(SONIOX_WEBSOCKET_URL)
            config_json = self._get_config(sample_rate)
            self.ws.send(json.dumps(config_json))
            
            print(f"[STT Provider: Soniox] Connected via WebSocket.")
            
            # Start background thread to listen for server responses
            self.message_thread = threading.Thread(target=self._message_handler, daemon=True)
            self.message_thread.start()
        except Exception as e:
            print(f"[STT Provider: Soniox] Failed to connect: {e}")
            self.close_connection()
            raise

    def send_audio_chunk(self, audio_chunk: bytes) -> None:
        """
        Sends raw PCM audio bytes to the connected WebSocket.
        """
        # Ensure we don't send if the app is shutting down or connection is closing
        if self.ws and not self._stop_event.is_set() and utils.app_running.is_set() and not self._connection_closed:
            try:
                self.ws.send(audio_chunk)
            except Exception as e:
                if utils.app_running.is_set() and not self._connection_closed:
                    print(f"[STT Provider: Soniox] Failed to send audio chunk: {e}")
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
                self.ws.close()
            except Exception:
                pass
            self.ws = None
            
        if self.message_thread and self.message_thread.is_alive():
            # Use a short join to ensure the message thread can exit its loop
            self.message_thread.join(timeout=1.5)
            
        print("[STT Provider: Soniox] Disconnected and cleaned up resources.")
