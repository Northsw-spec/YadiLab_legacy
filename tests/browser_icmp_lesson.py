"""Real Chromium and direct HTTP for the complete guided Echo lesson."""
from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from playwright.sync_api import expect, sync_playwright
from browser_smoke import ROOT, hold_http_reply, release_http_reply


HEADINGS = [
    "Om [observerat]:",
    "Då [vad det faktiskt betyder]:",
    "Möjliga orsaker [inte fastställda/hypoteser]:",
    "Vad detta inte bevisar:",
    "Nästa diagnostiska steg:",
    "Förväntat resultat och tolkning:",
    "Åtgärd [först efter fastställd orsak]:",
    "Verifiering [fungerar det nu?]:",
    "Beviskälla och begränsningar:",
]
START = "/api/icmp/investigation/start"
PROBE = "/api/icmp/investigation/probe"
DIAGNOSE = "/api/icmp/investigation/diagnose"
REPAIR = "/api/icmp/investigation/repair"
STOP = "/api/icmp/investigation/stop"


@contextmanager
def protected_process(directory, port=0):
    with subprocess.Popen(
        [sys.executable, "-m", "network_core", "--no-browser",
         "--port", str(port), "--data-dir", str(directory)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    ) as process:
        try:
            deadline = monotonic() + 10
            startup = b""
            while monotonic() < deadline:
                ready, _, _ = select.select([process.stdout], [], [], max(0, deadline - monotonic()))
                if not ready:
                    break
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    break
                startup += chunk
                address = re.search(rb"http://127\.0\.0\.1:(\d+)/\n", startup)
                key = re.search(rb"Local API access key \(this run only\): ([\w-]+)\n", startup)
                if address and key:
                    yield int(address[1]), key[1].decode("ascii")
                    return
            raise AssertionError("Protected application did not start")
        finally:
            process.terminate()
            process.wait(timeout=10)


def enter_workspace(page, port, key):
    page.goto(f"http://127.0.0.1:{port}/", wait_until="domcontentloaded")
    dialog = page.locator("#local-api-auth-dialog")
    expect(dialog).to_be_visible()
    page.locator("#local-api-access-key").fill(key)
    with page.expect_response(lambda r: r.url.endswith("/api/projects") and r.status == 200):
        page.locator("#local-api-auth-submit").click()
    expect(dialog).to_be_hidden()
    expect(page.locator("#local-api-access-key")).to_have_value("")
    page.locator("#toggle-dropdowns").click()


def show_sections(panel, count):
    expect(panel.locator("h4:visible")).to_have_text(HEADINGS[:count])


def validate_disclosure(data):
    assert "return-to-a" not in str(data)
    assert "RESTORE_STATIC_ROUTE" not in str(data)
    assert "STATIC_ROUTE_MISSING" not in str(data)
    assert "STATIC_NEXT_HOP_UNREACHABLE" not in str(data)
    assert "RESTORE_NEXT_HOP" not in str(data)
    assert "expectedNextHop" not in str(data)


def run_lesson(page, directory, lesson, filename):
    case_b = lesson == "echo-reply-b"
    reply_status = "ARP_FAILED" if case_b else "NO_ROUTE"
    right_diagnosis = "STATIC_NEXT_HOP_UNREACHABLE" if case_b else "STATIC_ROUTE_MISSING"
    wrong_diagnosis = "STATIC_ROUTE_MISSING" if case_b else "STATIC_NEXT_HOP_UNREACHABLE"
    panel = page.locator("#icmp-lesson")
    diagnose = page.locator("#icmp-investigation-diagnose")
    repair = page.locator("#icmp-investigation-repair")
    diagnosis = page.locator("#icmp-investigation-diagnosis")
    attempts_to_save = []
    def record_save(request):
        if request.url.endswith("/api/save"):
            attempts_to_save.append(request.method)

    page.on("request", record_save)

    def click_response(path, button, status=200):
        with page.expect_response("**" + path) as event:
            page.locator(button).click()
        response = event.value
        assert response.status == status
        return response.json()

    with page.expect_response("**/fixtures/icmp-echo-lesson.json") as fixture_response:
        page.locator("#icmp-lesson-load").click()
    fixture = fixture_response.value.json()
    expect(page.locator('[data-node-id="a"]')).to_have_count(1)
    expect(page.locator('[data-node-id="b"]')).to_have_count(1)
    target = directory / (filename + ".yadilab")
    assert not target.exists()

    page.locator("#project-filename").fill(filename)
    page.locator("#project-filename").press("Tab")
    saved = click_response("/api/save", "#save-project")
    original = target.read_bytes()
    digest = sha256(original).hexdigest()
    assert saved["project"] == fixture and saved["sha256"] == digest

    case_selector = page.locator("#icmp-lesson-case")
    case_selector.select_option(lesson)
    opening = click_response(START, "#icmp-lesson-start")
    assert opening["lesson"] == lesson
    expect(case_selector).to_be_disabled()
    validate_disclosure(opening)
    assert opening["openingObservation"] == {
        "replyMatched": False, "source": "SIMULATED",
    }
    for marker in ("NO_ROUTE", "ARP_FAILED", "203.0.113.254", "requestReceiver"):
        assert marker not in str(opening)
    show_sections(panel, 3)
    expect(panel).to_contain_text("Källan fick inget giltigt Echo Reply")
    opening_text = panel.locator("#icmp-lesson-symptom").inner_text()
    expect(panel.locator("#icmp-lesson-symptom")).not_to_contain_text("DELIVERED")
    expect(panel).to_contain_text("Vilken observation skulle tala emot din hypotes?")
    expect(diagnose).to_be_disabled()
    expect(repair).to_be_disabled()
    expect(page.locator("#icmp-lesson-action-text")).to_have_text("")
    review = page.locator("#icmp-lesson-review")
    hypotheses = panel.locator('input[name="icmp-lesson-hypothesis"]')
    tests = panel.locator('input[name="icmp-lesson-test"]')
    expect(hypotheses).to_have_count(3)
    expect(tests).to_have_count(3)
    expect(review).to_be_disabled()
    hypotheses.first.check()
    expect(review).to_be_disabled()  # A theory alone is not a test plan.
    tests.first.check()
    expect(review).to_be_enabled()
    page.locator("#icmp-lesson-reason").fill("En matchande route skulle tala emot min hypotes.")

    # Exercise the real server refusal despite the UI already disabling diagnoses.
    with page.expect_response("**" + DIAGNOSE) as early:
        result = page.evaluate('''async ({sessionId, project}) => {
          const {api} = await import('/services/api.js');
          try {
            await api('/api/icmp/investigation/diagnose',
              {sessionId, project, diagnosis: 'STATIC_ROUTE_MISSING'});
            return null;
          } catch (error) { return error.code; }
        }''', {"sessionId": opening["sessionId"], "project": fixture})
    assert result == "INVALID_PROJECT" and early.value.status == 422
    validate_disclosure(early.value.json())

    review.click()
    show_sections(panel, 5)
    expect(hypotheses.first).to_be_checked()
    expect(tests.first).to_be_checked()
    expect(hypotheses.first).to_be_disabled()
    expect(tests.first).to_be_disabled()
    expect(page.locator("#icmp-lesson-plan")).to_contain_text("Saknad aktiv returroute")
    expect(page.locator("#icmp-lesson-plan")).to_contain_text("Mätstatus: inte utförd")
    expect(page.locator("#icmp-lesson-plan")).to_contain_text("En matchande route")

    def probe(kind, node=None, destination=None, port=None):
        page.locator("#icmp-investigation-probe").select_option(kind)
        if node is not None:
            page.locator("#icmp-investigation-route-node").select_option(node)
            page.locator("#icmp-investigation-route-destination").select_option(destination)
        if port is not None:
            page.locator("#icmp-investigation-port").select_option(port)
        data = click_response(PROBE, "#icmp-investigation-measure")
        validate_disclosure(data)
        return data

    ping = probe("ping")["observation"]
    assert (ping["requestStatus"], ping["status"], ping["replyStatus"], ping["replyMatched"]) == (
        "DELIVERED", "REPLY_FAILED", reply_status, False)
    assert ping["requestReceiver"] == {"node": "b", "port": "eth0"}
    if case_b:
        step, = ping["replySteps"]
        assert step["arpStatus"] == "NO_REPLY" and step["transmissions"] == []
        assert step["nextHopIpv4"] == "203.0.113.254"
    else:
        assert ping["replySteps"] == []
    assert not probe("port", port='["b","eth0"]')["canDiagnose"]
    assert not probe("route", node="a", destination="source")["canDiagnose"]
    assert not probe("route", node="b", destination="destination")["canDiagnose"]
    diagnosis.select_option(wrong_diagnosis)
    expect(diagnose).to_be_disabled()
    show_sections(panel, 5)

    route = probe("route", node="b", destination="source")
    assert route["canDiagnose"]
    assert route["observation"]["status"] == ("MATCH" if case_b else "NO_ROUTE")
    if case_b:
        assert route["observation"]["selectedRoute"]["nextHop"] == "203.0.113.254"
    assert route["observation"]["destinationIpv4"] == "192.0.2.10"
    expect(page.locator("#icmp-lesson-plan")).to_contain_text("Mätstatus: utförd i simuleringen")
    show_sections(panel, 6)
    wrong = click_response(DIAGNOSE, "#icmp-investigation-diagnose")
    assert not wrong["correct"]
    validate_disclosure(wrong)
    expect(page.locator("#icmp-investigation-verdict")).to_contain_text("HYPOTES AVVISAD")
    expect(repair).to_be_disabled()

    diagnosis.select_option(right_diagnosis)
    correct = click_response(DIAGNOSE, "#icmp-investigation-diagnose")
    assert correct["correct"]
    validate_disclosure(correct)
    show_sections(panel, 7)
    expect(page.locator("#icmp-lesson-action-text")).not_to_contain_text("return-to-a")
    expect(page.locator("#icmp-lesson-verification-text")).to_have_text("")
    recovered = click_response(REPAIR, "#icmp-investigation-repair")
    assert (recovered["status"], recovered["failedEchoStatus"], recovered["restoredEchoStatus"],
            recovered["replyMatched"]) == ("RECOVERED", "REPLY_FAILED", "REPLIED", True)
    assert recovered["repair"]["routeId"] == "return-to-a"
    assert recovered["repair"]["scope"] == "PREVIEW_ONLY"
    assert recovered["repair"]["action"] == ("RESTORE_NEXT_HOP" if case_b else "RESTORE_STATIC_ROUTE")
    if case_b:
        assert recovered["repair"]["expectedNextHop"] == "203.0.113.1"
    assert recovered["verification"]["requestReceiver"] == {"node": "b", "port": "eth0"}
    assert recovered["verification"]["replyReceiver"] == {"node": "a", "port": "eth0"}
    show_sections(panel, 9)
    expect(page.locator("#icmp-lesson-action-text")).to_contain_text("return-to-a")
    expect(page.locator("#icmp-lesson-verification-text")).to_contain_text("REPLIED")
    expect(page.locator("#icmp-lesson-verification-text")).to_contain_text("a/eth0 (192.0.2.10)")

    click_response(STOP, "#icmp-investigation-stop")
    second = click_response(START, "#icmp-lesson-start")
    assert second["sessionId"] != opening["sessionId"]
    assert second["openingObservation"] == opening["openingObservation"]
    show_sections(panel, 3)
    expect(page.locator("#icmp-lesson-reason")).to_have_value("")
    expect(panel.locator('input[type="radio"]:checked')).to_have_count(0)
    expect(page.locator("#icmp-lesson-plan")).to_have_text("")
    expect(review).to_be_disabled()
    expect(page.locator("#icmp-lesson-action-text")).to_have_text("")
    hypotheses.nth(1).check()
    tests.nth(2).check()
    expect(review).to_be_enabled()
    review.click()
    expect(page.locator("#icmp-lesson-plan")).to_contain_text("Returroute finns men ARP-svar saknas")
    hold_http_reply(page, PROBE)
    page.locator("#icmp-investigation-probe").select_option("ping")
    page.locator("#icmp-investigation-measure").click()
    page.wait_for_function("window.__heldReply === true")
    with page.expect_response("**" + STOP) as stopped:
        page.locator("#new-project").click()
    assert stopped.value.status == 200
    expect(panel).to_be_hidden()
    expect(page.locator("#empty-state")).to_be_visible()
    release_http_reply(page)
    expect(page.locator("#icmp-investigation-status")).to_contain_text("Ingen ICMP-övning")
    expect(page.locator("#icmp-investigation-observations")).not_to_contain_text(reply_status)
    expect(page.locator("#icmp-lesson-plan")).to_have_text("")
    expect(diagnose).to_be_disabled()
    assert target.read_bytes() == original
    assert attempts_to_save == ["POST"]
    page.remove_listener("request", record_save)
    return fixture, original, digest, opening_text


def main():
    executable = shutil.which("chromium") or shutil.which("chromium-browser")
    with TemporaryDirectory() as temporary, sync_playwright() as playwright:
        directory = Path(temporary)
        browser = playwright.chromium.launch(headless=True, executable_path=executable)
        page = browser.new_page(viewport={"width": 1440, "height": 940})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        with protected_process(directory) as (port, first_key):
            enter_workspace(page, port, first_key)
            a = run_lesson(page, directory, "echo-reply", "echo-lesson")
            b = run_lesson(page, directory, "echo-reply-b", "echo-lesson-b")
            assert a == b  # Identical initial UI symptom and durable baseline.

        fixture, original, digest, _ = a
        with protected_process(directory, port) as (same_port, key):
            assert same_port == port and key != first_key
            enter_workspace(page, same_port, key)
            for filename in ("echo-lesson", "echo-lesson-b"):
                page.locator("#saved-projects").select_option(filename)
                with page.expect_response("**/api/projects/" + filename) as reopened:
                    page.locator("#open-project").click()
                assert reopened.value.status == 200
                payload = reopened.value.json()
                assert payload["project"] == fixture and payload["sha256"] == digest
                expect(page.locator("#project-name")).to_have_value(fixture["name"])
                expect(page.locator("#icmp-lesson")).to_be_hidden()
                assert (directory / (filename + ".yadilab")).read_bytes() == original
            assert not errors, errors
        browser.close()
        print("PASS real Chromium DIRECT_HTTP: both guided Echo cases, capability, stale reply, Save/Open after process restart")
        print("Saved project SHA-256:", digest)


if __name__ == "__main__":
    main()
