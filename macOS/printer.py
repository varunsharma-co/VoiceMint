"""Terminal transcript. Partials redraw one line; finals stay in the scrollback."""

from typing import TextIO

_CLEAR_TO_END = "\x1b[K"


class TranscriptPrinter:
    def __init__(self, writer: TextIO) -> None:
        self._writer = writer
        self._line_open = False

    def listening(self, device_name: str) -> None:
        self._write(f"Listening on {device_name}. Ctrl+C stops the session.\n")

    def partial_line(self, text: str) -> None:
        if text == "":
            return
        self._write(f"\r{text}{_CLEAR_TO_END}")
        self._line_open = True

    def final_utterance(self, text: str) -> None:
        if text == "":
            return
        self._write(f"\r{text}{_CLEAR_TO_END}\n")
        self._line_open = False

    def end_partial_line(self) -> None:
        if not self._line_open:
            return
        self._write("\n")
        self._line_open = False

    def error(self, text: str) -> None:
        self.end_partial_line()
        self._write(f"{text}\n")

    def _write(self, text: str) -> None:
        self._writer.write(text)
        self._writer.flush()
