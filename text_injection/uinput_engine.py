import time
from evdev import ecodes as e

from utils import get_logger
from .base import BaseInjector
from .virtual_keyboard import VirtualKeyboard

logger = get_logger(__name__)


class UInputInjector(BaseInjector):
    """
    Evdev-based text injection engine.
    Uses a shared VirtualKeyboard device to inject literal scancodes
    for zero-latency, clipboard-independent typing.
    """

    def __init__(self, vkb: VirtualKeyboard):
        super().__init__(vkb)
        logger.info("UInputInjector initialized using shared VirtualKeyboard.")

    def _get_keycode_and_shift(self, char: str) -> tuple[int | None, bool]:
        """Maps a character to its evdev keycode and shift requirement."""
        shift_required = False
        keycode = None

        if char.isalpha():
            keycode = getattr(e, f"KEY_{char.upper()}", None)
            if char.isupper():
                shift_required = True
        elif char.isdigit():
            keycode = getattr(e, f"KEY_{char}", None)
        else:
            # Common punctuation mapping
            char_map = {
                " ": (e.KEY_SPACE, False),
                ".": (e.KEY_DOT, False),
                ",": (e.KEY_COMMA, False),
                "-": (e.KEY_MINUS, False),
                "'": (e.KEY_APOSTROPHE, False),
                "/": (e.KEY_SLASH, False),
                "\\": (e.KEY_BACKSLASH, False),
                ";": (e.KEY_SEMICOLON, False),
                "=": (e.KEY_EQUAL, False),
                "`": (e.KEY_GRAVE, False),
                "[": (e.KEY_LEFTBRACE, False),
                "]": (e.KEY_RIGHTBRACE, False),
                "?": (e.KEY_SLASH, True),
                "!": (e.KEY_1, True),
                "@": (e.KEY_2, True),
                "#": (e.KEY_3, True),
                "$": (e.KEY_4, True),
                "%": (e.KEY_5, True),
                "^": (e.KEY_6, True),
                "&": (e.KEY_7, True),
                "*": (e.KEY_8, True),
                "(": (e.KEY_9, True),
                ")": (e.KEY_0, True),
                "_": (e.KEY_MINUS, True),
                "+": (e.KEY_EQUAL, True),
                "{": (e.KEY_LEFTBRACE, True),
                "}": (e.KEY_RIGHTBRACE, True),
                "|": (e.KEY_BACKSLASH, True),
                ":": (e.KEY_SEMICOLON, True),
                '"': (e.KEY_APOSTROPHE, True),
                "<": (e.KEY_COMMA, True),
                ">": (e.KEY_DOT, True),
                "~": (e.KEY_GRAVE, True),
            }
            if char in char_map:
                keycode, shift_required = char_map[char]

        return keycode, shift_required

    def inject(self, text: str) -> bool:
        """Types standard ASCII text sequentially at hardware speeds."""
        if not self.vkb or not self.vkb.ui:
            logger.error("Cannot inject: VirtualKeyboard is not initialized.")
            return False

        # Ensure trailing space is present exactly once
        text = text.rstrip(" ")
        if not text:
            return True
        text += " "

        try:
            for char in text:
                keycode, shift_required = self._get_keycode_and_shift(char)

                if keycode:
                    # 1. Press Shift if needed
                    if shift_required:
                        self.vkb.write_event(e.EV_KEY, e.KEY_LEFTSHIFT, 1)

                    # 2. Press and release the target key
                    self.vkb.write_event(e.EV_KEY, keycode, 1)
                    self.vkb.write_event(e.EV_KEY, keycode, 0)

                    # 3. Release Shift if it was pressed
                    if shift_required:
                        self.vkb.write_event(e.EV_KEY, e.KEY_LEFTSHIFT, 0)

                    # Tiny delay to ensure the OS kernel queue processes the stream reliably
                    time.sleep(0.01)

            return True

        except Exception as ex:
            logger.error(f"Error during uinput injection: {ex}")
            return False
