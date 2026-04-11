from abc import ABC, abstractmethod
from .virtual_keyboard import VirtualKeyboard

class BaseInjector(ABC):
    """
    Abstract Base Class for all text injection engines.
    
    Any new injection method (e.g., Clipboard, UInput, XDO Tool)
    must inherit from this class and implement the `inject` method.
    """

    def __init__(self, vkb: VirtualKeyboard):
        self.vkb = vkb

    @abstractmethod
    def inject(self, text: str) -> bool:
        """
        Injects the given text into the active OS cursor.

        Args:
            text (str): The final transcript text to inject.

        Returns:
            bool: True if injection was successful, False otherwise.
        """
        pass

    def close(self):
        """
        Optional cleanup method. Override this if the engine requires
        explicit teardown (like releasing virtual hardware).
        """
        pass
