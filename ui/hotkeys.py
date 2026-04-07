import threading
from pynput import keyboard

import config
import utils
from stt import start_listening, stop_listening

logger = utils.get_logger(__name__)

def _suppress_typed_character():
    """
    According to the pynput documentation: 
    'Hotkeys are not suppressed from other applications, as normal desktop environment hotkeys are.'
    To prevent the trigger key (e.g. 'u' or 'i') from appearing in the active window, 
    we use the pynput Controller to instantly emit a Backspace.
    Crucially, we must temporarily release the <cmd> (Super) modifier before backspacing, 
    otherwise X11 interprets it as Super+Backspace which fails to delete the character.
    """
    try:
        controller = keyboard.Controller()
        # Temporarily release the modifier so the Backspace registers as a raw text deletion
        controller.release(keyboard.Key.cmd)
        controller.tap(keyboard.Key.backspace)
    except Exception as ex:
        logger.error(f"Failed to suppress hotkey character via pynput Controller: {ex}")

def on_activate_start():
    """Triggered when the start hotkey is pressed."""
    _suppress_typed_character()
    if not utils.is_listening.is_set():
        logger.info("Hotkey triggered: START listening")
        # Start listening in a background thread so we don't block the hotkey listener
        threading.Thread(target=start_listening, daemon=True).start()

def on_activate_stop():
    """Triggered when the stop hotkey is pressed."""
    _suppress_typed_character()
    if utils.is_listening.is_set():
        logger.info("Hotkey triggered: STOP listening")
        # stop_listening() will stop the mic and close the websockets, unblocking the start_listening thread
        stop_listening()

def start_hotkey_listener():
    """Starts the global hotkey listener in a daemon thread using pynput.
    
    This implementation natively suppresses the hotkeys if the backend supports it (like X11).
    """
    hotkeys = {
        config.HOTKEY_START: on_activate_start,
        config.HOTKEY_STOP: on_activate_stop
    }
    
    try:
        listener = keyboard.GlobalHotKeys(hotkeys)
        listener.daemon = True
        listener.start()
        logger.info(f"Global hotkey listener started. Start: {config.HOTKEY_START}, Stop: {config.HOTKEY_STOP}")
        return listener
    except Exception as e:
        logger.error(f"Failed to start hotkey listener: {e}")
        return None
