import json
import threading
from typing import Optional
from urllib.parse import urlencode

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect, ClientConnection

import utils
from .base import BaseTranscriber, TranscriptCallback

# --- CONFIGURATION VARIABLES ---
# Base URL for the AssemblyAI real-time WebSocket API.
# v2 is standard: "wss://api.assemblyai.com/v2/realtime/ws"
# v3 is also supported by AssemblyAI: "wss://streaming.assemblyai.com/v3/ws"
ASSEMBLYAI_WS_BASE_URL = "wss://streaming.assemblyai.com/v3/ws"

# Use this to pass additional query parameters during connection.
# For example, if using v3, you might want to specify the speech model:
# EXTRA_QUERY_PARAMS = {"speech_model": "u3-rt-pro"}
EXTRA_QUERY_PARAMS = {"speech_model": "universal-streaming-english"}
# -------------------------------


class AssemblyAITranscriber(BaseTranscriber):
    """
    Implementation of the real-time transcriber for the AssemblyAI service.
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
                
                if "error" in res:
                    print(f"[STT Provider: AssemblyAI] Error: {res['error']}")
                    break

                # AssemblyAI uses 'message_type' (v2) or 'type' (v3)
                msg_type = res.get("message_type") or res.get("type")

                if msg_type == "SessionInformation":
                    print(f"[STT Provider: AssemblyAI] Session began.")
                elif msg_type == "Begin":
                    print(f"[STT Provider: AssemblyAI] Session began: ID={res.get('id')}")
                elif msg_type == "PartialTranscript":
                    transcript = res.get("text", "")
                    if transcript:
                        self.callback(transcript, False)
                elif msg_type == "FinalTranscript":
                    transcript = res.get("text", "")
                    if transcript:
                        self.callback(transcript, True)
                elif msg_type == "Turn":
                    # v3 specific
                    transcript = res.get("transcript", "")
                    end_of_turn = res.get("end_of_turn", False)
                    if transcript:
                        self.callback(transcript, end_of_turn)
                elif msg_type == "Termination":
                    print("[STT Provider: AssemblyAI] Session Terminated.")
                    break
                    
        except ConnectionClosed:
            if not self._connection_closed:
                print("[STT Provider: AssemblyAI] WebSocket connection closed by server.")
        except Exception as e:
            if utils.app_running.is_set() and not self._connection_closed:
                print(f"[STT Provider: AssemblyAI] Message handler error: {e}")
        finally:
            self._stop_event.set()

    def start_connection(self, sample_rate: int) -> None:
        """
        Initializes the WebSocket connection to AssemblyAI and starts the message loop.
        """
        self._stop_event.clear()
        self._connection_closed = False
        
        # Construct URL with query parameters
        params = {"sample_rate": sample_rate}
        params.update(EXTRA_QUERY_PARAMS)
        url = f"{ASSEMBLYAI_WS_BASE_URL}?{urlencode(params)}"
        
        try:
            # AssemblyAI authenticates via the Authorization header
            self.ws = connect(url, additional_headers={"Authorization": self.api_key})
            print(f"[STT Provider: AssemblyAI] Connected via WebSocket.")
            
            # Start background thread to listen for server responses
            self.message_thread = threading.Thread(target=self._message_handler, daemon=True)
            self.message_thread.start()
        except Exception as e:
            print(f"[STT Provider: AssemblyAI] Failed to connect: {e}")
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
                    print(f"[STT Provider: AssemblyAI] Failed to send audio chunk: {e}")
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
                # Send terminate session message if supported (v2 realtime)
                terminate_message = {"terminate_session": True}
                self.ws.send(json.dumps(terminate_message))
            except Exception:
                pass

            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None
            
        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=1.5)
            
        print("[STT Provider: AssemblyAI] Disconnected and cleaned up resources.")
