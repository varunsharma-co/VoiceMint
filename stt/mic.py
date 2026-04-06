import sys
import time

import sounddevice as sd

import config
import utils
from .silence import SilenceDetector
from .stt_providers import get_transcriber

def _on_silence_timeout() -> None:
    """Callback triggered by the silence detector daemon."""
    print(f"\n[Watchdog] {config.SILENCE_TIMEOUT_SECONDS}s of silence detected. Stopping listening.")
    stop_listening()

def stop_listening() -> None:
    """
    Gracefully stops the active audio capture and network streams
    by clearing the universal kill switch.
    """
    if utils.is_listening.is_set():
        utils.is_listening.clear()

def start_listening() -> None:
    """
    The main entry point for capturing audio.
    Instantiates the correct transcriber, starts the silence watchdog,
    and opens the sounddevice InputStream.
    Blocks until utils.is_listening is cleared.
    """
    if utils.is_listening.is_set():
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
        transcriber = get_transcriber(
            provider=config.ACTIVE_STT_PROVIDER,
            api_key=api_key,
            callback=_transcript_callback
        )
    except ValueError as e:
        print(f"\n[App] Error initializing STT provider: {e}")
        return

    # 4. Define Audio Capture Callback
    def audio_callback(indata, frames, time_info, status) -> None:
        if status:
            print(f"[Audio] Warning: {status}", file=sys.stderr)
        
        # Only forward audio if we are still marked as active
        if utils.is_listening.is_set():
            transcriber.send_audio_chunk(indata.tobytes())

    # 5. Start Execution Loop
    utils.is_listening.set()
    
    try:
        transcriber.start_connection(config.SAMPLE_RATE)
        silence_detector.start()

        # The context manager ensures hardware lock is released on exit/crash
        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            callback=audio_callback,
        ):
            print(f"\n[App] Listening via {config.ACTIVE_STT_PROVIDER.name}... (Press Ctrl+C to stop)")
            
            # Non-blocking sleep loop waiting for the global kill-switch
            while utils.is_listening.is_set():
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[App] Interrupted by user.")
        utils.is_listening.clear()
    except Exception as e:
        print(f"\n[App] A critical error occurred: {e}")
        utils.is_listening.clear()
    finally:
        # 6. Teardown
        silence_detector.cancel()
        transcriber.close_connection()
        print("\n[App] Stopped listening. Audio stream and network closed.")
