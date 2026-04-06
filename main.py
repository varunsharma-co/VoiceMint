import threading
import time

import config
import history
import utils
from stt import start_listening
from text_injection import close_injector, get_injector


def history_timer_loop() -> None:
    """A background daemon thread that flushes history every N minutes."""
    while True:
        time.sleep(config.HISTORY_SAVE_INTERVAL_MINUTES * 60)
        history.flush_history()


def queue_consumer() -> None:
    """
    A simple daemon thread that watches the transcript_queue.
    Whenever final text is deposited by the STT provider, it injects it into the OS
    and buffers it for session history.
    """
    injector = get_injector()
    session_text = ""

    while True:
        if not utils.transcript_queue.empty():
            text = utils.transcript_queue.get()
            print(f"\n\n[Main - Queue Consumer] FINAL TEXT RECEIVED. Injecting: \n{text}\n")
            injector.inject(text)
            
            # Accumulate text for the current session
            if session_text and not session_text.endswith(" "):
                session_text += " " + text.strip()
            else:
                session_text += text.strip()

        elif not utils.is_listening.is_set():
            # Trigger 3: Cleanup Flush
            if hasattr(injector, "flush"):
                injector.flush()
                
            # If the session ended, push the accumulated text to the history buffer
            if session_text.strip():
                history.add_session(session_text)
                session_text = ""  # Reset for the next session
        
        time.sleep(0.1)

if __name__ == "__main__":
    print("===================================================")
    print("🎤 VoiceMint STT Module Test")
    print("===================================================")
    print("This is a temporary main.py to test the STT package.")
    print("Speak into your microphone. Press Ctrl+C to exit.")
    print("===================================================\n")

    # Initialize the injector early to catch permission errors before starting the mic
    try:
        get_injector()
    except Exception as e:
        print(f"\n[App] Failed to initialize text injection: {e}")
        exit(1)

    # Start the history background timer
    timer_thread = threading.Thread(target=history_timer_loop, daemon=True)
    timer_thread.start()

    # Start the background consumer thread to inject finalized text and buffer history
    consumer_thread = threading.Thread(target=queue_consumer, daemon=True)
    consumer_thread.start()

    # Start the microphone and STT WebSocket stream.
    # This call will block the main thread until Ctrl+C is pressed or the silence timeout hits.
    start_listening()

    # Clean up the injector (virtual hardware) when exiting
    close_injector()

    print("\n[Main] Application exited cleanly.")
