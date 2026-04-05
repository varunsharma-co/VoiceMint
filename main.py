import threading
import time

import config
from stt import start_listening, stop_listening

def queue_consumer() -> None:
    """
    A simple daemon thread that watches the transcript_queue.
    Whenever final text is deposited by the STT provider, it prints it out.
    """
    while True:
        if not config.transcript_queue.empty():
            text = config.transcript_queue.get()
            print(f"\n\n[Main - Queue Consumer] FINAL TEXT RECEIVED: \n{text}\n")
        time.sleep(0.1)

if __name__ == "__main__":
    print("===================================================")
    print("🎤 VoiceMint STT Module Test")
    print("===================================================")
    print("This is a temporary main.py to test the STT package.")
    print("Speak into your microphone. Press Ctrl+C to exit.")
    print("===================================================\n")

    # Start the background consumer thread to print finalized text
    consumer_thread = threading.Thread(target=queue_consumer, daemon=True)
    consumer_thread.start()

    # Start the microphone and STT WebSocket stream.
    # This call will block the main thread until Ctrl+C is pressed or the silence timeout hits.
    start_listening()

    print("\n[Main] Application exited cleanly.")
