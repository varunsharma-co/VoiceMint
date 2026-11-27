import sys
import time
import queue
import threading
from typing import Optional

import sounddevice as sd

import config
import utils
from .silence import SilenceDetector
from .stt_providers import get_transcriber
from .stt_providers.base import BaseTranscriber

# Global reference to the active transcriber to allow forceful termination
_active_transcriber: Optional[BaseTranscriber] = None

def _on_silence_timeout() -> None:
    """Callback triggered by the silence detector daemon."""
    print(f"\n[Watchdog] {config.SILENCE_TIMEOUT_SECONDS}s of silence detected. Stopping listening.")
    try:
        from ui.tray import get_tray_manager
        tray = get_tray_manager()
        tray.handle_activation_request(activate=False, is_timeout=True)
    except Exception as e:
        print(f"Error signaling tray manager on timeout: {e}")
    stop_listening()

def stop_listening() -> None:
    """
    Gracefully (and forcefully) stops the active audio capture and network streams.
    Clears the kill switch and explicitly closes the transcriber connection.
    """
    global _active_transcriber
    
    if utils.is_listening.is_set():
        utils.is_listening.clear()
        
    utils.is_connected.clear()
    
    if _active_transcriber:
        # Forcefully close the connection to break any blocking WebSocket recv/send
        _active_transcriber.close_connection()
        _active_transcriber = None

def start_listening() -> None:
    """
    The main entry point for capturing audio.
    Instantiates the correct transcriber, starts the silence watchdog,
    and opens the sounddevice InputStream.
    Blocks until utils.is_listening is cleared or app_running is false.
    """
    global _active_transcriber

    if _active_transcriber:
        print("[App] Already listening. Ignoring duplicate start request.")
        return

    # 1. Fetch API Key and Initialize Watchdog
    api_key = config.STT_API_KEYS.get(config.ACTIVE_STT_PROVIDER)
    
    silence_detector = SilenceDetector(
        timeout=config.SILENCE_TIMEOUT_SECONDS,
        on_silence=_on_silence_timeout
    )

    # 2. Define the central text handling callback
    def _transcript_callback(transcript: str, is_final: bool) -> None:
        # Reset the watchdog timer whenever text is received
        silence_detector.reset()
        
        sys.stdout.write(f"\r[Client] Transcribing (Final: {is_final}): {transcript[:60]}...".ljust(100))
        sys.stdout.flush()
        
        if is_final:
            utils.transcript_queue.put(transcript)

    # 3. Instantiate Transcriber via Factory
    try:
        _active_transcriber = get_transcriber(
            provider=config.ACTIVE_STT_PROVIDER,
            api_key=api_key,
            callback=_transcript_callback
        )
    except ValueError as e:
        print(f"\n[App] Error initializing STT provider: {e}")
        return

    audio_queue: queue.Queue[bytes] = queue.Queue()

    # 4. Define Audio Capture Callback
    def audio_callback(indata, frames, time_info, status) -> None:
        if status:
            print(f"[Audio] Warning: {status}", file=sys.stderr)
        
        # Only forward audio if we are still active AND the app is running
        if utils.is_listening.is_set() and utils.app_running.is_set() and _active_transcriber:
            audio_queue.put(indata.tobytes())

    def send_loop() -> None:
        while utils.is_listening.is_set() and utils.app_running.is_set():
            try:
                # 100ms timeout lets us periodically check the is_listening flag
                chunk = audio_queue.get(timeout=0.1)
                if _active_transcriber:
                    _active_transcriber.send_audio_chunk(chunk)
            except queue.Empty:
                continue
            except Exception as ex:
                if utils.is_listening.is_set() and utils.app_running.is_set():
                    print(f"[Audio Sender] Error sending audio chunk: {ex}")

    # 5. Start Execution Loop
    utils.is_listening.set()
    utils.is_connected.clear()
    
    try:
        _active_transcriber.start_connection(config.SAMPLE_RATE)
        utils.is_connected.set()
        from ui.tray import get_tray_manager
        get_tray_manager().set_listening_active()
        
        # Spawn the background network sender thread
        threading.Thread(target=send_loop, daemon=True).start()
        
        silence_detector.start()

        # The context manager ensures hardware lock is released on exit/crash
        # Setting blocksize to 100ms of frames to optimize network streaming latency
        block_size = int(config.SAMPLE_RATE * 0.1)
        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=block_size,
            callback=audio_callback,
        ):
            print(f"\n[App] Listening via {config.ACTIVE_STT_PROVIDER.name}... (Press Ctrl+C to stop)")
            
            # Non-blocking sleep loop waiting for the global kill-switch or app shutdown
            while utils.is_listening.is_set() and utils.app_running.is_set():
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[App] Interrupted by user.")
        stop_listening()
    except Exception as e:
        print(f"\n[App] A critical error occurred: {e}")
        from ui.tray import get_tray_manager
        get_tray_manager().handle_activation_request(activate=False)
        stop_listening()
    finally:
        # 6. Teardown
        utils.is_connected.clear()
        silence_detector.cancel()
        if _active_transcriber:
            _active_transcriber.close_connection()
            _active_transcriber = None
        print("\n[App] Stopped listening. Audio stream and network closed.")
