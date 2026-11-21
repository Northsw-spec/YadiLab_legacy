"""Headed Chromium + real X11 PRIMARY selection integration regression.

Must run under xvfb-run with xclip installed. This deliberately tests the
system clipboard mechanism that headless browser smoke cannot reproduce.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore


def set_selection(name: str, text: str) -> None:
    # xclip deliberately forks to own the X11 selection until a receiver
    # requests it. Never use capture_output here: the daemon inherits the
    # stdout/stderr pipes and would keep subprocess.communicate() waiting.
    proc = subprocess.run(
        ["xclip", "-selection", name], input=text, text=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=10, check=False
    )
    assert proc.returncode == 0, (name, proc.returncode)
    read = subprocess.run(
        ["xclip", "-selection", name, "-o"], capture_output=True,
        text=True, timeout=5, check=False
    )
    assert read.returncode == 0 and read.stdout == text, (
        "X11 selection was not installed", name, read.returncode, read.stdout
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        server = LabHTTPServer(("127.0.0.1", 0), ProjectStore(Path(tmp)))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=False,
                    args=["--no-sandbox", "--ozone-platform=x11"]
                )
                try:
                    page = browser.new_page(viewport={"width": 1440, "height": 900})
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(f"http://127.0.0.1:{server.server_port}/",
                              wait_until="networkidle")
                    page.evaluate("""() => {
                      document.getElementById('arp-target-ip').closest('details').open = true;
                    }""")
                    field = page.locator("#arp-target-ip")
                    field.fill("192.0.2.20")
                    assert field.input_value() == "192.0.2.20"
                    svg = page.locator("#topology")
                    box = svg.bounding_box()
                    assert box and box["width"] >= 500, box
                    x = box["x"] + box["width"] - 42
                    y = box["y"] + box["height"] - 90
                    assert page.evaluate("""([x,y]) => {
                      const target = document.elementFromPoint(x, y);
                      const svg = document.getElementById('topology');
                      return target === svg || svg.contains(target);
                    }""", [x, y])

                    # Simulate text highlighted in an unrelated browser tab.
                    # PRIMARY is distinct from Ctrl+C's CLIPBOARD on X11.
                    set_selection("primary", "(vad jag anser)")
                    for i in range(2):
                        page.evaluate("""() => {
                          document.getElementById('arp-target-ip').focus({preventScroll:true});
                        }""")
                        assert page.evaluate("document.activeElement.id") == "arp-target-ip"
                        old_view = svg.get_attribute("viewBox")
                        page.mouse.move(x, y)
                        page.mouse.down(button="middle")
                        page.mouse.move(x + 26 + i * 10, y + 14 + i * 4, steps=3)
                        page.mouse.up(button="middle")
                        assert svg.get_attribute("viewBox") != old_view
                        assert field.input_value() == "192.0.2.20", (
                            "X11 PRIMARY middle paste corrupted ARP To field", field.input_value()
                        )

                    # Normal explicit CLIPBOARD paste remains functional.
                    set_selection("clipboard", "192.0.2.99")
                    field.focus()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Control+V")
                    assert field.input_value() == "192.0.2.99", (
                        "ordinary Ctrl+V was disabled", field.input_value()
                    )
                    assert errors == [], errors
                    print("PASS real X11 PRIMARY: 2 middle drags leave ARP To unchanged;"
                          " CLIPBOARD Ctrl+V works normally")
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=4)
            assert not worker.is_alive()


if __name__ == "__main__":
    run()
