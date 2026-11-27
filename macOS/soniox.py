"""Soniox socket port and the token assembler. The socket is a dumb byte transport."""

from websockets.sync.client import ClientConnection, connect

from constants import (
    PING_INTERVAL_SECONDS,
    PING_TIMEOUT_SECONDS,
    SONIOX_WEBSOCKET_URL,
)

_END_TOKEN = "<end>"


class SonioxSocket:
    """Sync WebSocket to Soniox. Close does not send an end-of-audio frame."""

    def __init__(self) -> None:
        self._ws: ClientConnection | None = None
        self._closed = False

    def connect(self) -> None:
        self._closed = False
        self._ws = connect(
            SONIOX_WEBSOCKET_URL,
            ping_interval=PING_INTERVAL_SECONDS,
            ping_timeout=PING_TIMEOUT_SECONDS,
        )

    def send_text(self, text: str) -> None:
        self._connection().send(text)

    def send_bytes(self, data: bytes) -> None:
        self._connection().send(data)

    def receive_text(self, timeout: float) -> str | None:
        try:
            message = self._connection().recv(timeout=timeout)
        except TimeoutError:
            return None
        if isinstance(message, bytes):
            return message.decode("utf-8")
        return message

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        ws = self._ws
        self._ws = None
        if ws is None:
            return
        try:
            # WebSocket close only. No empty text frame and no end-of-audio frame.
            ws.close()
        except Exception:
            pass

    def _connection(self) -> ClientConnection:
        if self._ws is None:
            raise ConnectionError("Soniox socket is not connected.")
        return self._ws


class TokenAssembler:
    """Linux token rules: accumulate finals, replace interim, drop `<end>`."""

    def __init__(self) -> None:
        self._committed: list[str] = []

    def apply(self, message: dict) -> tuple[str, bool] | None:
        interim: list[str] = []
        new_finals = 0
        tokens = message.get("tokens")
        if not isinstance(tokens, list):
            tokens = []

        for token in tokens:
            if not isinstance(token, dict):
                continue
            text = token.get("text")
            if not isinstance(text, str) or text == "" or text == _END_TOKEN:
                continue
            if token.get("is_final"):
                self._committed.append(text)
                new_finals += 1
            else:
                interim.append(text)

        rendered = "".join(self._committed) + "".join(interim)
        is_final = new_finals > 0 and not interim
        should_notify = rendered != "" or is_final
        if is_final:
            self._committed = []
        if not should_notify:
            return None
        return rendered, is_final
