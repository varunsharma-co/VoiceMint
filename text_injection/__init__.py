"""
Text Injection Package.
Exposes the core injection engines and manager based on the Facade pattern.
"""

from .base import BaseInjector
from .manager import close_injector, get_injector
from .uinput_engine import UInputInjector
from .virtual_keyboard import VirtualKeyboard

__all__ = [
    "BaseInjector",
    "UInputInjector",
    "get_injector",
    "close_injector",
    "VirtualKeyboard",
]
