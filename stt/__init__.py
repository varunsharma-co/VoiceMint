# Expose only the entry point function
from .mic import start_listening, stop_listening

__all__ = ["start_listening", "stop_listening"]
