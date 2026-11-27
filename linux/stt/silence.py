import threading
from typing import Callable, Optional

class SilenceDetector:
    """
    A daemon thread resettable timer that triggers a callback if not reset within the timeout period.
    """
    def __init__(self, timeout: float, on_silence: Callable[[], None]):
        self.timeout = timeout
        self.on_silence = on_silence
        self.timer: Optional[threading.Timer] = None

    def _trigger(self) -> None:
        self.on_silence()

    def start(self) -> None:
        """Starts the watchdog timer."""
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self._trigger)
        self.timer.daemon = True
        self.timer.start()

    def reset(self) -> None:
        """Resets the timer back to 0."""
        self.start()

    def cancel(self) -> None:
        """Permanently cancels the watchdog timer."""
        if self.timer:
            self.timer.cancel()
            self.timer = None
