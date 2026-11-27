"""The API key is read from the env file beside the app, not from the working directory."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from main import read_soniox_api_key


class EnvFileLocationTest(unittest.TestCase):
    def test_reads_the_env_file_beside_the_app_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_dir = root / "macOS"
            elsewhere = root / "elsewhere"
            app_dir.mkdir()
            elsewhere.mkdir()
            (app_dir / ".env").write_text("SONIOX_API_KEY=from-the-app-dir\n", encoding="utf-8")
            (elsewhere / ".env").write_text(
                "SONIOX_API_KEY=from-the-working-directory\n",
                encoding="utf-8",
            )

            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("SONIOX_API_KEY", None)
                original = os.getcwd()
                os.chdir(elsewhere)
                try:
                    key = read_soniox_api_key(app_dir.resolve())
                finally:
                    os.chdir(original)

        self.assertEqual(key, "from-the-app-dir")


if __name__ == "__main__":
    unittest.main()
