# Expose only the manager via the Facade Pattern
from .manager import get_transcriber

__all__ = ["get_transcriber"]
