import threading
import queue

# --- GLOBAL STATE FLAGS ---
# The universal kill switch.
# Controls the microphone loop, UI animations, and WebSocket connections.
is_listening = threading.Event()

# Thread-safe queue for final transcripts.
# STT providers push strings here, the injection engine pulls from here.
transcript_queue: queue.Queue[str] = queue.Queue()
