import time
import pyperclip
import subprocess
import shutil
from evdev import UInput
from evdev import ecodes as e

from config import (
    IDEAL_FLUSH_WORD_COUNT,
    FAILSAFE_FLUSH_MULTIPLIER,
    CLIPBOARD_RESTORE_DELAY_SEC,
)
from utils import get_logger
from .base import BaseInjector

logger = get_logger(__name__)


class ClipboardInjector(BaseInjector):
    """
    Clipboard-based text injection engine with a threaded chunked buffer.
    Accumulates incoming transcripts and bulk-pastes them using Shift+Insert 
    to prevent ghost pastes and handle non-standard punctuation.
    """

    def __init__(self):
        self.buffer: str = ""
        self.ui = None
        try:
            # Filter valid keys for the virtual device setup
            valid_keys = [v for k, v in e.ecodes.items() if k.startswith("KEY_") and v < 256]
            self.ui = UInput(events={e.EV_KEY: valid_keys}, name="voicemint-clipboard-keyboard")
            time.sleep(0.5)  # Wait a moment for the OS to register the new device
            logger.info("ClipboardInjector initialized successfully.")
        except PermissionError:
            logger.error("PermissionError: Access to /dev/uinput denied. Check udev rules.")
            raise
        except Exception as ex:
            logger.error(f"Failed to initialize ClipboardInjector: {ex}")
            raise

    def _ends_with_punctuation(self, text: str) -> bool:
        """Checks if text ends with a terminal punctuation mark."""
        text = text.strip()
        if not text:
            return False
        # Includes standard and Hindi terminal punctuation
        return text[-1] in [".", "?", "!", "।"]

    def _get_primary_selection(self) -> str:
        """Fetches the current X11/Wayland PRIMARY selection."""
        import os
        is_wayland = os.environ.get("WAYLAND_DISPLAY") is not None
        try:
            if is_wayland and shutil.which("wl-paste"):
                result = subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True)
                return result.stdout if result.returncode == 0 else ""
            if shutil.which("xclip"):
                result = subprocess.run(["xclip", "-selection", "primary", "-o"], capture_output=True, text=True)
                return result.stdout if result.returncode == 0 else ""
            if shutil.which("xsel"):
                result = subprocess.run(["xsel", "--primary", "--output"], capture_output=True, text=True)
                return result.stdout if result.returncode == 0 else ""
        except Exception as ex:
            logger.warning(f"Could not fetch primary selection: {ex}")
        return ""

    def _set_primary_selection(self, text: str):
        """Sets the X11/Wayland PRIMARY selection to ensure Shift+Insert works in terminals."""
        import os
        is_wayland = os.environ.get("WAYLAND_DISPLAY") is not None
        try:
            if is_wayland and shutil.which("wl-copy"):
                subprocess.run(["wl-copy", "--primary"], input=text.encode("utf-8"), check=True)
                return
            if shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "primary"], input=text.encode("utf-8"), check=True)
                return
            if shutil.which("xsel"):
                subprocess.run(["xsel", "--primary", "--input"], input=text.encode("utf-8"), check=True)
                return
        except Exception as ex:
            logger.warning(f"Failed to set primary selection: {ex}")

    def inject(self, text: str) -> bool:
        """
        Accumulates text in the buffer and checks flush conditions.
        """
        if not text:
            return True

        # Append the incoming transcript
        if self.buffer and not self.buffer.endswith(" "):
             self.buffer += " " + text.strip()
        else:
             self.buffer += text.strip()

        word_count = len(self.buffer.split())

        # Trigger 1: Ideal Flush (Threshold + Punctuation)
        if word_count >= IDEAL_FLUSH_WORD_COUNT and self._ends_with_punctuation(self.buffer):
            logger.info(f"Trigger 1 (Ideal) hit: {word_count} words.")
            return self.flush()

        # Trigger 2: Failsafe Flush (Hard Limit)
        if word_count >= (IDEAL_FLUSH_WORD_COUNT * FAILSAFE_FLUSH_MULTIPLIER):
            logger.info(f"Trigger 2 (Failsafe) hit: {word_count} words.")
            return self.flush()

        return True

    def flush(self) -> bool:
        """
        Executes the Ghost Paste Prevention Sequence.
        """
        if not self.buffer.strip():
            return True

        if not self.ui:
            logger.error("Cannot flush: UInput device is not initialized.")
            return False

        payload = self.buffer.strip() + " "
        self.buffer = ""  # Clear buffer immediately to prevent duplicate flushes

        try:
            # 1. Backup
            backup_clipboard = ""
            backup_primary = ""
            try:
                backup_clipboard = pyperclip.paste()
                backup_primary = self._get_primary_selection()
            except Exception as ex:
                logger.warning(f"Could not backup clipboards: {ex}")

            # 2. Load
            pyperclip.copy(payload)
            self._set_primary_selection(payload)

            # 3. Wait
            time.sleep(0.05)

            # 4. Paste (Shift + Insert)
            self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
            self.ui.syn()
            self.ui.write(e.EV_KEY, e.KEY_INSERT, 1)
            self.ui.write(e.EV_KEY, e.KEY_INSERT, 0)
            self.ui.syn()
            self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
            self.ui.syn()

            # 5. Wait
            time.sleep(CLIPBOARD_RESTORE_DELAY_SEC)

            # 6. Restore
            try:
                pyperclip.copy(backup_clipboard)
                self._set_primary_selection(backup_primary)
            except Exception as ex:
                logger.warning(f"Could not restore clipboards: {ex}")

            logger.info(f"Successfully pasted {len(payload.split())} words.")
            return True

        except Exception as ex:
            logger.error(f"Error during clipboard flush: {ex}")
            return False

    def close(self):
        """Releases virtual hardware and flushes any remaining text."""
        # Cleanup flush
        if self.buffer.strip():
            logger.info("Executing Cleanup Flush during close().")
            self.flush()

        if self.ui:
            self.ui.close()
            self.ui = None
            logger.info("ClipboardInjector closed and virtual device released.")
