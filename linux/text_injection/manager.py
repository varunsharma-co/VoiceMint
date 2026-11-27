from utils import get_logger
from config import ACTIVE_INJECTION_METHOD, InjectionMethod
from .base import BaseInjector
from .uinput_engine import UInputInjector
from .clipboard_engine import ClipboardInjector
from .virtual_keyboard import VirtualKeyboard

logger = get_logger(__name__)

# Global cache for the active injector to avoid re-initializing logic
_active_injector = None


def get_injector(vkb: VirtualKeyboard = None) -> BaseInjector:
    """
    Factory function that returns the active text injector instance.
    Initializes the engine on first call and returns the cached instance subsequently.
    
    Args:
        vkb (VirtualKeyboard): The shared virtual keyboard instance. 
                               Mandatory on the first call.
    """
    global _active_injector

    if _active_injector is not None:
        return _active_injector

    if vkb is None:
        raise ValueError("VirtualKeyboard instance must be provided on the first call to get_injector().")

    logger.info(f"Initializing text injection engine: {ACTIVE_INJECTION_METHOD.value}")

    if ACTIVE_INJECTION_METHOD == InjectionMethod.UINPUT:
        _active_injector = UInputInjector(vkb)
    elif ACTIVE_INJECTION_METHOD == InjectionMethod.CLIPBOARD:
        _active_injector = ClipboardInjector(vkb)
    else:
        logger.warning(
            f"Unsupported injection method: {ACTIVE_INJECTION_METHOD}, defaulting to UInput."
        )
        _active_injector = UInputInjector(vkb)

    return _active_injector


def close_injector():
    """Properly closes and releases resources for the active injector logic."""
    global _active_injector
    if _active_injector:
        try:
            _active_injector.close()
        except Exception as e:
            logger.error(f"Error closing injector: {e}")
        finally:
            _active_injector = None
