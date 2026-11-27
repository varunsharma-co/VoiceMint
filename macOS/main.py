"""Run a live transcript from the default microphone."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from microphone import DefaultMicrophone
from session import DictationSession
from soniox import SonioxSocket


def read_soniox_api_key(app_dir: Path) -> str:
    """Load SONIOX_API_KEY from the env file in `app_dir`.

    The path is the app directory, so the working directory does not matter.
    An already-set environment variable is left as it is.
    """
    load_dotenv(app_dir / ".env")
    return os.environ.get("SONIOX_API_KEY", "")


def main() -> int:
    api_key = read_soniox_api_key(Path(__file__).resolve().parent)
    session = DictationSession(
        api_key=api_key,
        audio=DefaultMicrophone(),
        socket=SonioxSocket(),
        writer=sys.stdout,
    )
    return session.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
