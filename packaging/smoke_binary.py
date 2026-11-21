"""Run the frozen executable and verify the real HTTP API and disk persistence."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def get(base: str, route: str) -> bytes:
    with urlopen(base + route, timeout=4) as response:
        assert response.status == 200, (route, response.status)
        return response.read()


def post(base: str, route: str, payload: dict) -> dict:
    req = Request(base + route, data=json.dumps(payload).encode('utf-8'),
                  headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(req, timeout=5) as response:
        assert response.status == 200, (route, response.status)
        return json.load(response)


def main() -> None:
    exe = Path(sys.argv[1]).resolve()
    assert exe.is_file(), f'Executable missing: {exe}'
    with tempfile.TemporaryDirectory() as temp:
        store = Path(temp) / 'projects'
        base = 'http://127.0.0.1:18765'
        with (Path(temp) / 'stdout.txt').open('wb') as stdout, (Path(temp) / 'stderr.txt').open('wb') as stderr:
            process = subprocess.Popen([str(exe), '--no-browser', '--port', '18765',
                                        '--data-dir', str(store)], stdout=stdout, stderr=stderr)
            try:
                for _ in range(90):
                    if process.poll() is not None:
                        raise AssertionError(f'Executable exited early: {process.returncode}')
                    try:
                        health = json.loads(get(base, '/api/health'))
                        break
                    except (OSError, URLError):
                        time.sleep(0.3)
                else:
                    raise AssertionError('Executable HTTP startup timed out')
                assert health == {'app':'Network Lab', 'version':'0.1.0', 'storage':'local'}, health
                assert b'Network Lab' in get(base, '/')
                assert b'packetJourneyFrames' in get(base, '/canvas.js')
                assert b'function render()' in get(base, '/app.js')
                assert b'.workspace' in get(base, '/styles.css')
                assert b'.send-address-pair' in get(base, '/styles.css')
                assert b'id="toggle-dropdowns"' in get(base, '/')
                assert b'id="probe-from-ip"' in get(base, '/')
                assert b'id="probe-destination"' in get(base, '/')
                assert b'setupAddressBindings' in get(base, '/app.js')
                sample = json.loads(Path('examples/explicit-three-device-demo.yadilab').read_text(encoding='utf-8'))
                saved = post(base, '/api/save', {'filename':'frozen-smoke',
                                                 'project': sample, 'expectedSha256':None})
                assert len(saved['sha256']) == 64
                loaded = json.loads(get(base, '/api/projects/frozen-smoke'))
                assert loaded['project'] == saved['project']
                assert (store / 'frozen-smoke.yadilab').is_file()
                assert json.loads(get(base, '/api/projects'))['projects'][0]['filename'] == 'frozen-smoke'
                print('PASS frozen binary: health, UI, JS/CSS, explicit disk Save/Open')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if process.returncode not in (0, -15):
                    print((Path(temp) / 'stderr.txt').read_text(errors='replace')[-6000:], file=sys.stderr)

if __name__ == '__main__':
    main()
