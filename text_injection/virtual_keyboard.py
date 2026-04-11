import time
import threading
from typing import Optional
from evdev import UInput, ecodes as e

from utils import get_logger

logger = get_logger(__name__)

class VirtualKeyboard:
    """
    A thread-safe Context Manager for the Linux evdev.UInput virtual keyboard.
    Ensures a single instance is shared and properly released.
    """
    def __init__(self, name: str = "voicemint-virtual-keyboard"):
        self.name = name
        self.ui: Optional[UInput] = None
        self._lock = threading.Lock()

    def __enter__(self):
        """Initializes the virtual hardware device."""
        try:
            # Filter valid keys for a standard keyboard setup
            valid_keys = [v for k, v in e.ecodes.items() if k.startswith("KEY_") and v < 256]
            self.ui = UInput(events={e.EV_KEY: valid_keys}, name=self.name)
            
            # Wait a moment for the OS to register the new device
            time.sleep(0.5)
            logger.info(f"VirtualKeyboard '{self.name}' initialized successfully via Context Manager.")
            return self
        except PermissionError:
            logger.error("PermissionError: Access to /dev/uinput denied. Run with sudo or configure udev rules!")
            raise
        except Exception as ex:
            logger.error(f"Failed to initialize VirtualKeyboard: {ex}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Releases the virtual hardware device."""
        if self.ui:
            self.ui.close()
            self.ui = None
            logger.info(f"VirtualKeyboard '{self.name}' closed and resources released.")

    def write_event(self, type: int, code: int, value: int):
        """Thread-safe raw event write."""
        if not self.ui:
            logger.error("VirtualKeyboard: Cannot write, device not initialized.")
            return

        with self._lock:
            self.ui.write(type, code, value)
            self.ui.syn()

    def tap_key(self, keycode: int):
        """Thread-safe key tap (press and release)."""
        if not self.ui:
            return

        with self._lock:
            self.ui.write(e.EV_KEY, keycode, 1)
            self.ui.write(e.EV_KEY, keycode, 0)
            self.ui.syn()

    def simulate_shift_insert(self):
        """Specialized thread-safe Shift+Insert paste sequence."""
        if not self.ui:
            return

        with self._lock:
            self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
            self.ui.syn()
            self.ui.write(e.EV_KEY, e.KEY_INSERT, 1)
            self.ui.write(e.EV_KEY, e.KEY_INSERT, 0)
            self.ui.syn()
            self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
            self.ui.syn()
