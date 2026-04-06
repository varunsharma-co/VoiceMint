import logging

from config import ACTIVE_INJECTION_METHOD, InjectionMethod
from .base import BaseInjector
from .uinput_engine import UInputInjector

logger = logging.getLogger(__name__)

# Global cache for the active injector to avoid re-initializing virtual hardware
_active_injector = None


def get_injector() -> BaseInjector:
    """
    Factory function that returns the active text injector instance.
    Initializes the engine on first call and returns the cached instance subsequently.
    """
    global _active_injector

    if _active_injector is not None:
        return _active_injector

    logger.info(f"Initializing text injection engine: {ACTIVE_INJECTION_METHOD.value}")

    if ACTIVE_INJECTION_METHOD == InjectionMethod.UINPUT:
        _active_injector = UInputInjector()
    else:
        logger.warning(
            f"Unsupported injection method: {ACTIVE_INJECTION_METHOD}, defaulting to UInput."
        )
        _active_injector = UInputInjector()

    return _active_injector


def close_injector():
    """Properly closes and releases resources for the active injector."""
    global _active_injector
    if _active_injector:
        try:
            _active_injector.close()
        except Exception as e:
            logger.error(f"Error closing injector: {e}")
        finally:
            _active_injector = None
