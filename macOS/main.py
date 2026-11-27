"""Run a live transcript from the default microphone."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from microphone import DefaultMicrophone
from session import DictationSession
from soniox import SonioxSocket


def main() -> int:
    app_dir = Path(__file__).resolve().parent
    load_dotenv(app_dir / ".env")
    api_key = os.environ.get("SONIOX_API_KEY", "")
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
