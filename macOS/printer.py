"""Terminal transcript. Partials redraw one line; each final is the next line."""

from typing import TextIO

_CLEAR_TO_END = "\x1b[K"
_PARTIAL = "[PARTIAL] "
_FINAL = "[FINAL] "


class TranscriptPrinter:
    def __init__(self, writer: TextIO) -> None:
        self._writer = writer
        self._line_open = False
        self._partial = ""

    def listening(self, device_name: str) -> None:
        self._write(f"Listening on {device_name}. Ctrl+C stops the session.\n")

    def partial_line(self, text: str) -> None:
        if text == "":
            return
        self._partial = text
        self._write(f"\r{_PARTIAL}{text}{_CLEAR_TO_END}")
        self._line_open = True

    def final_utterance(self, text: str) -> None:
        if text == "":
            return
        # Leave the latest partial in the scrollback, then print the final
        # underneath it and leave a blank line for the next utterance.
        if self._line_open:
            self._write("\n")
        self._partial = ""
        self._line_open = False
        self._write(f"{_FINAL}{text}\n\n")

    def end_partial_line(self) -> None:
        if not self._line_open:
            return
        self._write("\n")
        self._line_open = False
        self._partial = ""

    def redraw(self) -> None:
        """Rewrite the open partial so a stderr warning does not leave it torn."""
        if not self._line_open or self._partial == "":
            return
        self._write(f"\r{_PARTIAL}{self._partial}{_CLEAR_TO_END}")

    def error(self, text: str) -> None:
        self.end_partial_line()
        self._write(f"{text}\n")

    def _write(self, text: str) -> None:
        self._writer.write(text)
        self._writer.flush()
