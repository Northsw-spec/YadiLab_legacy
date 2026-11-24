"""Real Chromium: unauthenticated localhost cannot read projects; browser
must enter a process-scoped key before Save/Open succeeds.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from test_model import example


def main():
    key = "R" * 43  # Fake test token; normal CLI uses a CSPRNG.
    with tempfile.TemporaryDirectory() as directory:
        server = LabHTTPServer(("127.0.0.1", 0), ProjectStore(Path(directory)),
                               auth_token=key)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            try:
                urlopen(url + "/api/projects", timeout=4)
                raise AssertionError("unauthenticated read of private projects")
            except HTTPError as error:
                assert error.code == 401
                assert json.loads(error.read())["error"] == "AUTH_REQUIRED"

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.goto(url + "/", wait_until="domcontentloaded")
                    assert key not in page.url
                    assert key not in page.content()

                    # Launch an actual same-origin module call, but do not
                    # await it: the dialog must appear before it resolves.
                    page.evaluate('''() => {
                        window.__authResult = null;
                        import('/services/api.js').then(module =>
                          module.api('/api/projects')).then(result => {
                            window.__authResult = result;
                          }).catch(error => {
                            window.__authResult = {error: error.message};
                          });
                    }''')
                    dialog = page.locator("#local-api-auth-dialog")
                    dialog.wait_for(state="visible", timeout=12000)
                    page.locator("#local-api-access-key").fill(key)
                    page.locator("#local-api-auth-submit").click()
                    dialog.wait_for(state="hidden", timeout=12000)
                    page.wait_for_function("window.__authResult !== null", timeout=12000)
                    assert page.evaluate("window.__authResult") == {"projects": []}
                    assert page.locator("#local-api-access-key").input_value() == ""
                    assert key not in page.url

                    loaded = page.evaluate('''async (project) => {
                        const {api} = await import('/services/api.js');
                        const saved = await api('/api/save', {
                          filename: 'explicit', project, expectedSha256: null,
                        });
                        const opened = await api('/api/projects/explicit');
                        return {sha: saved.sha256, opened};
                    }''', example())
                    assert loaded["opened"]["project"] == example()
                    assert server.store.read("explicit")["sha256"] == loaded["sha"]
                    assert not dialog.is_visible()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=4)


if __name__ == "__main__":
    main()
