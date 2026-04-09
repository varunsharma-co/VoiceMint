import threading
import time
import sys
import os

import history
import utils
from text_injection import close_injector, get_injector
import ui
import stt

def queue_consumer() -> None:
    """
    A persistent daemon thread that watches the transcript_queue.
    Checks utils.app_running to ensure a graceful exit.
    """
    injector = get_injector()
    session_text = ""

    while utils.app_running.is_set() or not utils.transcript_queue.empty():
        if not utils.transcript_queue.empty():
            text = utils.transcript_queue.get()
            print(f"\n[Consumer] FINAL TEXT: {text}")
            injector.inject(text)
            
            if session_text and not session_text.endswith(" "):
                session_text += " " + text.strip()
            else:
                session_text += text.strip()

        elif not utils.is_listening.is_set():
            if hasattr(injector, "flush"):
                injector.flush()
                
            if session_text.strip():
                history.add_session(session_text)
                session_text = ""
        
        time.sleep(0.1)
    
    # Final flush on exit
    if session_text.strip():
        history.add_session(session_text)
    
    print("[Consumer] Exited gracefully.")

if __name__ == "__main__":
    utils.enforce_single_instance()
    utils.app_running.set()

    print("===================================================")
    print("🎤 VoiceMint Starting...")
    print("===================================================")

    try:
        get_injector()
    except Exception as e:
        print(f"\n[App] Failed to initialize text injection: {e}")
        sys.exit(1)

    history.start_background_timer()

    # Consumer thread
    consumer_thread = threading.Thread(target=queue_consumer, daemon=False)
    consumer_thread.start()

    # Tray on background thread (it manages its own GLib/GTK context)
    tray_manager = ui.get_tray_manager()
    tray_thread = threading.Thread(target=tray_manager.run, daemon=True)
    tray_thread.start()

    # Hotkey listener
    listener = ui.start_hotkey_listener()

    print("[Main] System Tray and background workers active.")
    
    # Launch UI on Main Thread (CustomTkinter/Tkinter REQUIRE this on Linux/X11)
    try:
        ui.launch_ui()
    except KeyboardInterrupt:
        utils.app_running.clear()

    # --- CLEANUP SEQUENCE ---
    print("\n[Main] Initiating graceful cleanup...")
    
    # Give a split-second for any final notifications/sounds (e.g. from Tray Quit) to spawn
    time.sleep(0.5)
    
    utils.app_running.clear()
    
    # 1. Forcefully stop dictation if active (WebSocket connection closed violently)
    stt.stop_listening()

    # 2. Wait for consumer to finish final history writes
    consumer_thread.join(timeout=2.0)

    # 3. Clean up virtual hardware
    close_injector()
    
    # 4. Stop hotkey listener
    if listener is not None:
        listener.stop()

    # 5. Clean up RAM assets
    tray_manager.cleanup_ram_assets()

    # 6. Remove lock file
    if os.path.exists(utils.LOCK_FILE):
        try:
            os.remove(utils.LOCK_FILE)
            print("[Main] Lock file removed.")
        except Exception as e:
            print(f"[Main] Failed to remove lock file: {e}")

    print("[Main] Application exited cleanly.")
