import threading
import time
import sys
import fcntl
import os

import history
import utils
from text_injection import close_injector, get_injector
import ui

LOCK_FILE = "/tmp/voicemint.lock"
_lock_fd = None

def enforce_single_instance():
    global _lock_fd
    _lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("An instance of VoiceMint is already running.")
        # Optional: Show a messagebox if needed, but since it's a background CLI primarily, exiting is fine.
        sys.exit(0)

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
    enforce_single_instance()

    print("===================================================")
    print("🎤 VoiceMint Starting...")
    print("===================================================")

    # Initialize the injector early to catch permission errors before starting the app
    try:
        get_injector()
    except Exception as e:
        print(f"\n[App] Failed to initialize text injection: {e}")
        sys.exit(1)

    # Start the history background timer
    history.start_background_timer()

    # Start the background consumer thread to inject finalized text and buffer history
    consumer_thread = threading.Thread(target=queue_consumer, daemon=True)
    consumer_thread.start()

    # Start global hotkey listener
    listener = ui.start_hotkey_listener()

    # Start GUI on main thread
    ui.launch_ui()

    # Clean up the injector (virtual hardware) when exiting
    close_injector()
    
    # Also stop hotkey listener
    if listener is not None:
        listener.stop()

    print("\n[Main] Application exited cleanly.")
