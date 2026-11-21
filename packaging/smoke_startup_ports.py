"""Black-box startup tests against the actual PyInstaller executable."""
from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

PORT = 8765


def main() -> None:
    binary = Path(sys.argv[1]).resolve()
    assert binary.is_file(), binary
    with tempfile.TemporaryDirectory() as tmp:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", PORT))
            occupied.listen(1)
            # Explicitly chosen ports must fail instead of switching.
            exact = subprocess.run(
                [str(binary), "--no-browser", "--port", str(PORT),
                 "--data-dir", str(Path(tmp) / "explicit")],
                capture_output=True, text=True, timeout=25, check=False,
            )
            assert exact.returncode == 2, (
                "explicit occupied port must exit 2: ", exact.returncode, exact.stderr)
            assert "already in use" in exact.stderr, exact.stderr
            assert "Traceback" not in exact.stderr, exact.stderr
            assert "_cleanup_thread" not in exact.stderr, exact.stderr

            # Omitting --port should automatically bind to 8766..8774 and
            # tell users which URL to open, with a real HTTP health response.
            proc = subprocess.Popen(
                [str(binary), "--no-browser", "--data-dir", str(Path(tmp) / "default")],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            found = None
            try:
                for _ in range(120):
                    if proc.poll() is not None:
                        raise AssertionError(f"frozen binary exited early: {proc.returncode}")
                    for port in range(PORT + 1, PORT + 10):
                        try:
                            with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=.3) as response:
                                data = json.load(response)
                            if data.get("storage") == "local" and data.get("version") == "0.1.0":
                                found = port
                                break
                        except OSError:
                            continue
                    if found is not None:
                        break
                    time.sleep(.25)
                assert found is not None, "no live HTTP fallback from frozen executable"
            finally:
                proc.terminate()
                try:
                    stdout, stderr = proc.communicate(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    stdout, stderr = proc.communicate(timeout=8)
            assert f"at http://127.0.0.1:{found}/" in stdout, stdout
            assert f"Port {PORT} is busy; using port {found}" in stderr, stderr
            assert "Traceback" not in stderr, stderr
            print("PASS frozen startup: occupied explicit port fails cleanly, "
                  f"default falls back to {found}, real HTTP health responds")


if __name__ == "__main__":
    main()
