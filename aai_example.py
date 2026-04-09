import json
import os
import queue
import threading
from urllib.parse import urlencode

import sounddevice as sd
from dotenv import load_dotenv
from websockets.sync.client import connect

# Load environment variables
load_dotenv()
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# --- Configuration ---
SAMPLE_RATE = 16000
CHANNELS = 1
# 100ms chunks (0.1s * 16000Hz = 1600 samples)
FRAMES_PER_BUFFER = 1600 

# V3 Configuration from documentation
CONNECTION_PARAMS = {
    "speech_model": "u3-rt-pro",
    "sample_rate": SAMPLE_RATE,
}
API_ENDPOINT = f"wss://streaming.assemblyai.com/v3/ws?{urlencode(CONNECTION_PARAMS)}"

stop_event = threading.Event()
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """Callback for sounddevice to capture audio."""
    if status:
        print(f"Status: {status}")
    if not stop_event.is_set():
        # AssemblyAI V3 expects raw binary PCM16LE
        audio_queue.put(bytes(indata))

def message_handler(ws):
    """Handles incoming messages from AssemblyAI."""
    try:
        for message in ws:
            if stop_event.is_set():
                break
            
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "SessionBegun":
                print(f"\n[AssemblyAI] Session began: ID={data.get('session_id')}")
            elif msg_type == "Turn":
                transcript = data.get("transcript", "")
                is_final = data.get("end_of_turn", False)
                
                if is_final:
                    # Clear the line and print final transcript
                    print("\r" + " " * 80 + "\r", end="")
                    print(f"Final: {transcript}")
                else:
                    # Print interim transcript
                    print(f"\rInterim: {transcript}", end="", flush=True)
            elif msg_type == "SessionTerminated":
                print("\n[AssemblyAI] Session terminated.")
                break
    except Exception as e:
        if not stop_event.is_set():
            print(f"\n[AssemblyAI] Message handler error: {e}")

def run():
    if not API_KEY:
        print("Error: ASSEMBLYAI_API_KEY not found in .env")
        return

    print(f"Connecting to: {API_ENDPOINT}")
    
    headers = {
        "Authorization": API_KEY
    }

    try:
        # Using websockets.sync.client.connect (as in soniox.py)
        with connect(API_ENDPOINT, additional_headers=headers) as ws:
            print("Connected to AssemblyAI.")
            
            # Start message handler thread
            msg_thread = threading.Thread(target=message_handler, args=(ws,))
            msg_thread.daemon = True
            msg_thread.start()

            # Start audio capture
            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=FRAMES_PER_BUFFER,
                dtype="int16",
                channels=CHANNELS,
                callback=audio_callback,
            ):
                print("Recording... Press Ctrl+C to stop.")
                while not stop_event.is_set():
                    try:
                        # Pull from queue and send to websocket
                        chunk = audio_queue.get(timeout=0.1)
                        # AssemblyAI V3: Send audio data as binary message
                        ws.send(chunk)
                    except queue.Empty:
                        continue
                    except KeyboardInterrupt:
                        break

            # Send termination message
            print("\nStopping...")
            stop_event.set()
            ws.send(json.dumps({"type": "Terminate"}))
            print("Sent Terminate message.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        stop_event.set()
        print("Test complete.")

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        stop_event.set()
        print("\nExited.")
