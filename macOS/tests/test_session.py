"""Dictation session behavior, driven through fake ports and the transcript writer."""

import contextlib
import io
import json
import threading
import unittest

from session import AudioSource, ByteSocket, DictationSession

_LISTENING = "Listening on Test Input. Ctrl+C stops the session.\n"


class ScriptedAudio:
    """Default-input stand-in. `read` blocks until the next chunk or `close`."""

    def __init__(self, chunks: list[bytes] | None = None) -> None:
        self._chunks = list(chunks or [])
        self._closed = threading.Event()
        self.open_calls = 0
        self.close_calls = 0

    def open(self) -> str:
        self.open_calls += 1
        return "Test Input"

    def read(self, timeout: float) -> bytes | None:
        if self._chunks:
            return self._chunks.pop(0)
        self._closed.wait(timeout)
        return None

    def close(self) -> None:
        self.close_calls += 1
        self._closed.set()


class ScriptedSocket:
    """Byte-socket stand-in. Queued exceptions are raised from `receive_text`."""

    def __init__(self, incoming: list[str | None | BaseException] | None = None) -> None:
        self._incoming = list(incoming or [])
        self._closed = threading.Event()
        self.connect_calls = 0
        self.close_calls = 0
        self.texts: list[str] = []
        self.payloads: list[bytes] = []
        self.receive_calls = 0
        self.fail_connect: BaseException | None = None
        self.fail_send_text: BaseException | None = None
        self.fail_send_bytes: BaseException | None = None

    def connect(self) -> None:
        self.connect_calls += 1
        if self.fail_connect is not None:
            raise self.fail_connect

    def send_text(self, text: str) -> None:
        if self.fail_send_text is not None:
            raise self.fail_send_text
        self.texts.append(text)

    def send_bytes(self, data: bytes) -> None:
        self.payloads.append(data)
        if self.fail_send_bytes is not None:
            raise self.fail_send_bytes

    def receive_text(self, timeout: float) -> str | None:
        self.receive_calls += 1
        if self._incoming:
            item = self._incoming.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item
        if self.receive_calls > 100:
            raise RuntimeError("session kept listening with nothing left to receive")
        self._closed.wait(timeout)
        return None

    def close(self) -> None:
        self.close_calls += 1
        self._closed.set()


def run_session(
    api_key: str,
    audio: AudioSource,
    socket: ByteSocket,
) -> tuple[int, str]:
    writer = io.StringIO()
    session = DictationSession(
        api_key=api_key,
        audio=audio,
        socket=socket,
        writer=writer,
    )
    return session.run(), writer.getvalue()


class MissingApiKeyTest(unittest.TestCase):
    def test_missing_key_names_the_variable_and_opens_neither_port(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(incoming=[KeyboardInterrupt()])

        code, output = run_session("", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(output, "SONIOX_API_KEY is missing.\n")
        self.assertEqual(audio.open_calls, 0)
        self.assertEqual(socket.connect_calls, 0)


class BlankApiKeyTest(unittest.TestCase):
    def test_blank_key_fails_the_same_way_as_a_missing_one(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(incoming=[KeyboardInterrupt()])

        code, output = run_session("   ", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(output, "SONIOX_API_KEY is missing.\n")
        self.assertEqual(audio.open_calls, 0)
        self.assertEqual(socket.connect_calls, 0)


class FailedHandshakeTest(unittest.TestCase):
    def test_connect_failure_prints_one_error_and_never_opens_the_microphone(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket()
        socket.fail_connect = ConnectionError("handshake rejected")

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(output, "Could not reach Soniox: handshake rejected\n")
        self.assertEqual(audio.open_calls, 0)
        self.assertGreaterEqual(socket.close_calls, 1)

    def test_config_send_failure_prints_one_error_and_never_opens_the_microphone(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket()
        socket.fail_send_text = ConnectionError("config rejected")

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(output, "Could not reach Soniox: config rejected\n")
        self.assertEqual(audio.open_calls, 0)
        self.assertEqual(socket.connect_calls, 1)
        self.assertGreaterEqual(socket.close_calls, 1)


class HandshakeInterruptTest(unittest.TestCase):
    def test_ctrl_c_during_connect_exits_successfully_without_opening_the_microphone(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket()
        socket.fail_connect = KeyboardInterrupt()

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(audio.open_calls, 0)

    def test_ctrl_c_during_config_send_exits_successfully_without_opening_the_microphone(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket()
        socket.fail_send_text = KeyboardInterrupt()

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(audio.open_calls, 0)
        self.assertEqual(socket.connect_calls, 1)


class SonioxErrorTest(unittest.TestCase):
    def test_error_code_skips_tokens_prints_one_error_and_exits(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(
            incoming=[
                json.dumps(
                    {
                        "error_code": 503,
                        "error_message": "over capacity",
                        "tokens": [{"text": "nope", "is_final": True}],
                        "finished": True,
                    }
                ),
                KeyboardInterrupt(),
            ]
        )

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(
            output,
            _LISTENING + "Soniox error 503: over capacity\n",
        )
        self.assertNotIn("nope", output)
        self.assertEqual(socket.connect_calls, 1)
        self.assertGreaterEqual(audio.close_calls, 1)
        self.assertGreaterEqual(socket.close_calls, 1)


class UnexpectedCloseTest(unittest.TestCase):
    def test_unexpected_close_prints_one_error_releases_the_microphone_and_exits(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(incoming=[ConnectionError("reset by peer")])

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(
            output,
            _LISTENING + "Soniox connection closed: reset by peer\n",
        )
        self.assertEqual(socket.connect_calls, 1)
        self.assertGreaterEqual(audio.close_calls, 1)
        self.assertGreaterEqual(socket.close_calls, 1)


class _TimeoutsThenStop(ScriptedSocket):
    """Returns timeouts immediately, then Ctrl+C, so a missed send failure cannot hang."""

    def receive_text(self, timeout: float) -> str | None:
        self.receive_calls += 1
        if self.receive_calls > 50:
            raise KeyboardInterrupt()
        return None


class SendFailureTest(unittest.TestCase):
    def test_send_failure_prints_one_error_closes_both_ports_and_exits(self) -> None:
        audio = ScriptedAudio(chunks=[b"\x01\x00"])
        socket = _TimeoutsThenStop()
        socket.fail_send_bytes = ConnectionError("broken pipe")
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 1)
        self.assertEqual(
            output,
            _LISTENING + "Could not send audio to Soniox: broken pipe\n",
        )
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(socket.payloads, [b"\x01\x00"])
        self.assertEqual(socket.connect_calls, 1)
        self.assertGreaterEqual(audio.close_calls, 1)
        self.assertGreaterEqual(socket.close_calls, 1)


class FinishedMessageTest(unittest.TestCase):
    def test_finished_applies_tokens_in_that_message_then_exits_successfully(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(
            incoming=[
                json.dumps(
                    {
                        "tokens": [
                            {"text": "Hello", "is_final": True},
                            {"text": " there", "is_final": True},
                        ],
                        "finished": True,
                    }
                ),
                json.dumps({"tokens": [{"text": "EXTRA", "is_final": True}]}),
                KeyboardInterrupt(),
            ]
        )

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 0)
        self.assertEqual(output, _LISTENING + "\rHello there\x1b[K\n")
        self.assertNotIn("EXTRA", output)
        self.assertEqual(socket.receive_calls, 1)
        self.assertEqual(socket.connect_calls, 1)

    def test_finished_applies_partial_tokens_before_exiting(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(
            incoming=[
                json.dumps(
                    {
                        "tokens": [{"text": "still talking", "is_final": False}],
                        "finished": True,
                    }
                ),
                KeyboardInterrupt(),
            ]
        )

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 0)
        self.assertEqual(output, _LISTENING + "\rstill talking\x1b[K\n")
        self.assertEqual(socket.receive_calls, 1)


class _DropWhenClosed(ScriptedSocket):
    """The in-flight send fails once `close` runs, and `close` itself fails too."""

    def __init__(self) -> None:
        super().__init__()
        self._send_entered = threading.Event()
        self.saw_drop_after_close = False

    def send_bytes(self, data: bytes) -> None:
        self.payloads.append(data)
        self._send_entered.set()
        if not self._closed.wait(timeout=0.5):
            raise TimeoutError("send was not unblocked by close")
        self.saw_drop_after_close = True
        raise ConnectionError("closed by session")

    def receive_text(self, timeout: float) -> str | None:
        self.receive_calls += 1
        if not self._send_entered.wait(timeout=2):
            raise RuntimeError("sender did not start")
        raise KeyboardInterrupt()

    def close(self) -> None:
        super().close()
        raise ConnectionError("close failed")


class CloseAlreadyStartedTest(unittest.TestCase):
    def test_socket_drop_from_our_close_does_not_replace_success(self) -> None:
        audio = ScriptedAudio(chunks=[b"\x01\x00"])
        socket = _DropWhenClosed()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 0)
        self.assertEqual(output, _LISTENING)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(socket.saw_drop_after_close)
        self.assertEqual(socket.connect_calls, 1)
        self.assertGreaterEqual(audio.close_calls, 1)
        self.assertGreaterEqual(socket.close_calls, 1)


class QuietRoomTest(unittest.TestCase):
    def test_silence_keeps_the_session_open_until_the_user_stops_it(self) -> None:
        audio = ScriptedAudio()
        socket = ScriptedSocket(incoming=[None, None, None, KeyboardInterrupt()])

        code, output = run_session("test-key", audio, socket)

        self.assertEqual(code, 0)
        self.assertEqual(output, _LISTENING)
        self.assertEqual(socket.receive_calls, 4)
        self.assertEqual(socket.connect_calls, 1)
        self.assertGreaterEqual(audio.close_calls, 1)
        self.assertGreaterEqual(socket.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
