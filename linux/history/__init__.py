"""
Session History Package.
Exposes the core history saving logic based on the Facade pattern.
"""
from .history import add_session, flush_history, start_background_timer, get_recent_history

__all__ = ["add_session", "flush_history", "start_background_timer", "get_recent_history"]
