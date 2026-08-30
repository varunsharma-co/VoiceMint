# STT Provider Integration Guide (`Adding_New_STT_Provider.md`)

This document serves as the **master architectural blueprint and implementation manual** for creating, refactoring, or auditing Speech-to-Text (STT) providers in **VoiceMint**.

Any human engineer or AI assistant working on the audio capture and transcription pipeline must follow the structural rules, design patterns, and file modification steps detailed below to maintain compatibility, stability, and high performance across the entire application lifecycle.

---

## 1. Architectural Overview & Design Patterns

### 1.1 Decoupled Hardware vs. Network Architecture
VoiceMint strictly decouples hardware audio recording from network streaming and transcription:
- **Audio Capture & Watchdog ([stt/mic.py](stt/mic.py), [stt/silence.py](stt/silence.py))**:
  - Operates PortAudio via `sounddevice.InputStream`.
  - Captures 16-bit signed PCM mono audio (`int16`, 1 channel) at the configured sample rate (`config.SAMPLE_RATE`, typically `16000` Hz).
  - Pushes raw audio chunks into an in-memory queue (`audio_queue`) inside the high-priority PortAudio callback (`<1µs` return time).
  - Runs a silence detection daemon timer ([stt/silence.py](stt/silence.py)) that triggers an auto-stop callback when no speech/transcript is detected for `config.SILENCE_TIMEOUT_SECONDS`.
- **Audio Sender Thread ([stt/mic.py](stt/mic.py))**:
  - Pops raw byte chunks from `audio_queue` and calls `_active_transcriber.send_audio_chunk(chunk)`.
  - Buffers any network latency spikes safely in memory without blocking hardware recording frames or overflowing PortAudio buffers.
- **STT Providers Subsystem ([stt/stt_providers/](stt/stt_providers/))**:
  - **Zero hardware audio dependencies**: STT provider classes NEVER interact with microphones or sound drivers directly.
  - Dedicated entirely to WebSocket connection management, authentication, protocol serialization/deserialization, background message receiving, and routing text to the callback.

```text
[Microphone] 
     │ (PortAudio callback / sounddevice)
     ▼
[audio_queue]
     │ (send_loop() thread)
     ▼
[STT Provider: send_audio_chunk()] 
     │ (WebSocket sync client)
     ▼
[Cloud STT API: Soniox / AssemblyAI / New Provider]
     │ (WebSocket server streaming response)
     ▼
[STT Provider: _message_handler() thread]
     │ (self.callback(transcript, is_final))
     ▼
[utils.transcript_queue]
     │ (queue_consumer() in main.py)
     ▼
[Text Injector: uinput / clipboard]
```

### 1.2 The Facade Pattern & Package Routing
VoiceMint enforces package isolation using the Facade Pattern via `__init__.py` files:
1. **[stt/\_\_init\_\_.py](stt/__init__.py)** exposes only the high-level orchestrator functions:
   - `start_listening()`
   - `stop_listening()`
2. **[stt/stt_providers/\_\_init\_\_.py](stt/stt_providers/__init__.py)** exposes only the factory interface:
   - `get_transcriber()`
3. Individual provider modules (e.g., `soniox.py`, `assembly.py`, `modulate.py`) are strictly internal to [stt/stt_providers/](stt/stt_providers/) and are only instantiated through [stt/stt_providers/manager.py](stt/stt_providers/manager.py).

---

## 2. STT Provider Commonalities & Strict Invariants

Every STT provider in VoiceMint must adhere to the contract established in [stt/stt_providers/base.py](stt/stt_providers/base.py) and follow the exact synchronization patterns below.

### 2.1 The `BaseTranscriber` Contract
All providers must subclass `BaseTranscriber`:

```python
# stt/stt_providers/base.py
from abc import ABC, abstractmethod
from typing import Callable

TranscriptCallback = Callable[[str, bool], None]

class BaseTranscriber(ABC):
    def __init__(self, api_key: str, callback: TranscriptCallback):
        self.api_key = api_key
        self.callback = callback

    @abstractmethod
    def start_connection(self, sample_rate: int) -> None:
        """Initializes the WebSocket connection and starts the message receiving thread."""
        pass

    @abstractmethod
    def send_audio_chunk(self, audio_chunk: bytes) -> None:
        """Streams a chunk of raw PCM audio bytes to the remote provider."""
        pass

    @abstractmethod
    def close_connection(self) -> None:
        """Cleanly closes the network connection and terminates the background message thread."""
        pass
```

### 2.2 Standard Internal State Variables
Every provider class must maintain the following internal instance attributes in its `__init__`:
- `self._stop_event: threading.Event = threading.Event()`: Cooperative cancellation flag for the receiving thread.
- `self._connection_closed: bool = True`: Boolean tracking whether the connection is active or terminated (starts `True`, set to `False` on `start_connection()`).
- `self.ws: Optional[ClientConnection] = None`: Synchronous WebSocket client connection instance (`websockets.sync.client.ClientConnection`).
- `self.message_thread: Optional[threading.Thread] = None`: Reference to the background daemon thread executing `_message_handler()`.

### 2.3 WebSocket Connection Standards
- **Client Library**: VoiceMint uses `websockets.sync.client.connect` (standard synchronous WebSocket client from `websockets` library).
- **Keepalive Ping/Pong**: Always pass `ping_interval=config.WEBSOCKET_PING_INTERVAL` and `ping_timeout=config.WEBSOCKET_PING_TIMEOUT` to `connect(...)`. Because raw audio is streamed continuously every 100ms, TCP keepalives are managed cleanly, preventing proactive `1011 keepalive ping timeout` errors under GIL contention.
- **Clean Failure Recovery**: If `start_connection()` encounters an exception during connection setup or handshake, it must call `self.close_connection()` before re-raising the exception.

### 2.4 The Message Receiving Loop Pattern (`_message_handler`)
The message receiver executes in a dedicated background daemon thread. It must follow this pattern:
1. **Cancellation & Lifecycle Checks**: Check `while not self._stop_event.is_set() and utils.app_running.is_set():`.
2. **Timeout Handling**: Call `self.ws.recv(timeout=1.0)` wrapped in a `try...except TimeoutError: continue` block so the thread can react to `_stop_event` or application shutdown promptly.
3. **Connection Closure Handling**: Catch `ConnectionClosed` exceptions and suppress log noise if `self._connection_closed` is already `True`.
4. **Guaranteed Cleanup**: Set `self._stop_event.set()` in the `finally:` block.

### 2.5 Transcript Callback Routing
The callback signature is `self.callback(transcript: str, is_final: bool)`:
- **Interim Transcripts (`is_final=False`)**: Sent to display real-time terminal output and reset the silence watchdog timer in [stt/mic.py](stt/mic.py).
- **Final Transcripts (`is_final=True`)**: Sent when a speech endpoint or finalized phrase is committed by the STT engine. In [stt/mic.py](stt/mic.py), only finalized text (`is_final=True`) is pushed to `utils.transcript_queue` to be typed at the OS cursor.

### 2.6 Idempotent Teardown Pattern (`close_connection`)
`close_connection()` must be completely idempotent (safe to call multiple times from different threads):
1. Check `if self._connection_closed: return` and immediately set `self._connection_closed = True`.
2. Set `self._stop_event.set()`.
3. Send server-specific termination message if required by the API (e.g. `{"terminate_session": True}` for AssemblyAI).
4. Close `self.ws` inside a `try...except` block and set `self.ws = None`.
5. Join `self.message_thread` with a timeout (e.g., `self.message_thread.join(timeout=1.5)`).

---

## 3. Comparison of Current Providers

| Dimension | Soniox ([soniox.py](stt/stt_providers/soniox.py)) | AssemblyAI ([assembly.py](stt/stt_providers/assembly.py)) |
| :--- | :--- | :--- |
| **WebSocket URL** | `wss://stt-rt.soniox.com/transcribe-websocket` | `wss://streaming.assemblyai.com/v3/ws` |
| **Authentication** | Sent inside initial configuration JSON payload (`"api_key": ...`) | Sent via HTTP Request Headers (`additional_headers={"Authorization": api_key}`) |
| **Configuration Delivery** | First JSON message sent over WebSocket after connect (`ws.send(json.dumps(config))`) | Query parameters in WebSocket URL (`urlencode(...)`) |
| **Endpoint / Silence Control** | `"enable_endpoint_detection": True`, `"max_endpoint_delay_ms": config.SPEECH_ENDPOINT_DELAY_MS` | Query param `end_utterance_silence_threshold=config.SPEECH_ENDPOINT_DELAY_MS` |
| **Transcript Payload Structure** | Stream of token dictionaries (`tokens: [{"text": "...", "is_final": True/False}]`). Accumulates non-final and final tokens. Strips `<end>` endpointing token. | JSON messages containing `"type"` or `"message_type"`. Dispatches `"PartialTranscript"`, `"FinalTranscript"`, `"Turn"`, `"Begin"`, `"Termination"`. |
| **Session Termination** | Disconnects WebSocket directly. | Sends `{"terminate_session": True}` before closing WebSocket. |

---

## 4. Step-by-Step Checklist: Adding a New STT Provider

Follow these exact steps to add a new STT provider (e.g., `Deepgram` or any custom provider `FooBar`):

```text
Checklist Overview:
[ ] Step 1: Add Provider to Enum & Secrets in config.py
[ ] Step 2: Update .env.example & .env
[ ] Step 3: Create Transcriber Class in stt/stt_providers/<provider_name>.py
[ ] Step 4: Register Provider in stt/stt_providers/manager.py
[ ] Step 5: Add Provider to Settings UI Combobox in ui/settings_ui.py
[ ] Step 6: (Optional) Set as Active Provider in config.json
[ ] Step 7: Update Documentation in GEMINI.md
```

---

### Step 1: Update [config.py](config.py)

1. Add the new provider identifier to the `STTProvider` enum:
   ```python
   class STTProvider(Enum):
       SONIOX = "soniox"
       MODULATE = "modulate"
       ASSEMBLYAI = "assemblyai"
       FOOBAR = "foobar"  # <--- Add new provider (lowercase string)
   ```

2. Load the provider's API key from environment variables:
   ```python
   _SONIOX_API_KEY = os.getenv("SONIOX_API_KEY")
   _MODULATE_API_KEY = os.getenv("MODULATE_API_KEY")
   _ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
   _FOOBAR_API_KEY = os.getenv("FOOBAR_API_KEY")  # <--- Add API key variable
   ```

3. Register the key in the `STT_API_KEYS` dictionary:
   ```python
   STT_API_KEYS = {
       STTProvider.SONIOX: _SONIOX_API_KEY,
       STTProvider.MODULATE: _MODULATE_API_KEY,
       STTProvider.ASSEMBLYAI: _ASSEMBLYAI_API_KEY,
       STTProvider.FOOBAR: _FOOBAR_API_KEY,  # <--- Map Enum to key
   }
   ```

---

### Step 2: Update [.env.example](.env.example) and `.env`

1. In [.env.example](.env.example), add the template entry:
   ```bash
   SONIOX_API_KEY=your_soniox_key_here
   ASSEMBLYAI_API_KEY=your_assemblyai_key_here
   FOOBAR_API_KEY=your_foobar_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```

2. In your local `.env` file (untracked), add your actual API key:
   ```bash
   FOOBAR_API_KEY=sk_live_12345...
   ```

---

### Step 3: Create `stt/stt_providers/<provider_name>.py`

Create a new file (e.g. `stt/stt_providers/foobar.py`) following the boilerplate provided in [Section 5](#5-production-ready-starter-template).

Key implementation checklist for this class:
- [ ] Subclasses `BaseTranscriber`.
- [ ] Uses `websockets.sync.client.connect`.
- [ ] Passes `config.WEBSOCKET_PING_INTERVAL` and `config.WEBSOCKET_PING_TIMEOUT`.
- [ ] Applies `config.SPEECH_ENDPOINT_DELAY_MS` to the provider's silence/endpointing setting.
- [ ] Manages `_stop_event`, `_connection_closed`, and `message_thread`.
- [ ] Correctly fires `self.callback(transcript, is_final)`.
- [ ] Implements idempotent `close_connection()`.

---

### Step 4: Register Provider in [stt/stt_providers/manager.py](stt/stt_providers/manager.py)

1. Import the new transcriber class:
   ```python
   from .foobar import FoobarTranscriber
   ```

2. Add the factory dispatch branch inside `get_transcriber()`:
   ```python
   def get_transcriber(provider: STTProvider, api_key: Optional[str], callback: TranscriptCallback) -> BaseTranscriber:
       if not api_key:
           raise ValueError(f"API key for {provider.name} is missing or invalid.")
           
       if provider == STTProvider.SONIOX:
           return SonioxTranscriber(api_key=api_key, callback=callback)
       elif provider == STTProvider.ASSEMBLYAI:
           return AssemblyAITranscriber(api_key=api_key, callback=callback)
       elif provider == STTProvider.FOOBAR:
           return FoobarTranscriber(api_key=api_key, callback=callback)
       
       raise ValueError(f"Unsupported streaming STT provider: {provider.value}")
   ```

---

### Step 5: Update Settings UI in [ui/settings_ui.py](ui/settings_ui.py)

Update the combobox values in `_build_app_tab()` to include the capitalized provider name:
```python
# In SettingsPanel._build_app_tab()
self.stt_menu = ttk.Combobox(
    self.tab_app,
    textvariable=self.stt_var,
    values=["Soniox", "Modulate", "Assemblyai", "Foobar"],  # <--- Add Foobar
    state="readonly"
)
```

---

### Step 6: (Optional) Set as Active Provider in `config.json`

To make the new provider active by default, edit `config.json`:
```json
{
  "ACTIVE_STT_PROVIDER": "foobar",
  ...
}
```

---

### Step 7: Update System Documentation in [GEMINI.md](GEMINI.md)

1. Update the **Tech Stack / STT Providers** section.
2. Update the visual directory tree to list the new `stt/stt_providers/<provider_name>.py` file.
3. Add a summary bullet describing the provider in the file descriptions.

---

## 5. Production-Ready Starter Template

Below is the complete, typed boilerplate template for creating a new STT provider file (`stt/stt_providers/<provider_name>.py`):

```python
import json
import threading
from typing import Optional
from urllib.parse import urlencode

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect, ClientConnection

import utils
import config
from .base import BaseTranscriber, TranscriptCallback

# Define the WebSocket endpoint for the streaming STT provider
PROVIDER_WEBSOCKET_URL = "wss://api.example.com/v1/streaming-transcribe"


class NewSTTTranscriber(BaseTranscriber):
    """
    Implementation of real-time streaming Speech-to-Text for [Provider Name].
    Decoupled from audio capture; receives raw audio chunks via send_audio_chunk().
    """

    def __init__(self, api_key: str, callback: TranscriptCallback):
        super().__init__(api_key, callback)
        self._stop_event = threading.Event()
        self.ws: Optional[ClientConnection] = None
        self.message_thread: Optional[threading.Thread] = None
        self._connection_closed = True  # Start in closed state

    def _message_handler(self) -> None:
        """
        Background loop reading incoming WebSocket frames and invoking callback.
        Runs in a dedicated daemon thread.
        """
        if not self.ws:
            return

        try:
            while not self._stop_event.is_set() and utils.app_running.is_set():
                try:
                    # Timeout allows periodically re-checking stop_event and app_running
                    message = self.ws.recv(timeout=1.0)
                except TimeoutError:
                    continue

                res = json.loads(message)

                # 1. Check for API-level error responses
                if res.get("error"):
                    print(f"[STT Provider: NewSTT] Error: {res['error']}")
                    break

                # 2. Extract transcript and finalization status
                # (Adapt this logic to the provider's specific JSON schema)
                transcript_text = res.get("text", "")
                is_final = res.get("is_final", False)

                if transcript_text:
                    self.callback(transcript_text, is_final)

                # 3. Check for session termination signals
                if res.get("is_session_finished"):
                    print("[STT Provider: NewSTT] Session completed by server.")
                    break

        except ConnectionClosed:
            if not self._connection_closed:
                print("[STT Provider: NewSTT] WebSocket connection closed by server.")
        except Exception as e:
            if utils.app_running.is_set() and not self._connection_closed:
                print(f"[STT Provider: NewSTT] Message handler error: {e}")
        finally:
            self._stop_event.set()

    def start_connection(self, sample_rate: int) -> None:
        """
        Establishes WebSocket connection and launches the receiver thread.
        """
        self._stop_event.clear()
        self._connection_closed = False

        # Format URL parameters or request headers based on API spec
        params = {
            "sample_rate": sample_rate,
            "endpoint_delay_ms": config.SPEECH_ENDPOINT_DELAY_MS,
        }
        full_url = f"{PROVIDER_WEBSOCKET_URL}?{urlencode(params)}"

        try:
            # Connect synchronously with configured keepalive settings
            self.ws = connect(
                full_url,
                additional_headers={"Authorization": f"Bearer {self.api_key}"},
                ping_interval=config.WEBSOCKET_PING_INTERVAL,
                ping_timeout=config.WEBSOCKET_PING_TIMEOUT,
            )
            print("[STT Provider: NewSTT] Connected via WebSocket.")

            # Spawn background daemon receiver thread
            self.message_thread = threading.Thread(target=self._message_handler, daemon=True)
            self.message_thread.start()
        except Exception as e:
            print(f"[STT Provider: NewSTT] Failed to connect: {e}")
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
                    print(f"[STT Provider: NewSTT] Failed to send audio chunk: {e}")
                self._stop_event.set()

    def close_connection(self) -> None:
        """
        Idempotent teardown: closes socket, notifies server, and joins receiver thread.
        """
        if self._connection_closed:
            return

        self._connection_closed = True
        self._stop_event.set()

        if self.ws:
            try:
                # Send graceful termination message if required by the API
                self.ws.send(json.dumps({"type": "CloseStream"}))
            except Exception:
                pass

            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=1.5)

        print("[STT Provider: NewSTT] Disconnected and cleaned up resources.")
```

---

## 6. Testing & Validation Checklist

Before submitting a new STT provider integration, perform these verification checks:
1. **Activation & Connecting State**:
   - Start voice typing (via Super+U or UI Start button).
   - Verify the tray icon turns yellow (`icon-connecting-128.png`) and the UI displays `Connecting...`.
2. **Active State & Sound**:
   - Verify that upon WebSocket handshake completion, the icon turns green (`icon-on-128.png`), `start.wav` plays, and notification `Listening via <Provider>...` appears.
3. **Live Streaming & Silence Watchdog**:
   - Speak a sentence. Verify terminal prints interim transcribing logs: `[Client] Transcribing (Final: False): ...`.
   - Pause speaking for longer than `config.SILENCE_TIMEOUT_SECONDS` (default 45s). Verify silence detector watchdog automatically stops recording and plays `stop.wav`.
4. **Text Injection & Normalization**:
   - Speak sentences consecutively. Verify finalized text is injected into the active text field with correct trailing space separation.
5. **Clean Disconnection & Shutdown**:
   - Press Super+I or UI Stop button. Verify `stop.wav` plays, tray icon turns red (`icon-off-128.png`), and `close_connection()` completes cleanly with no lingering threads or socket errors.
