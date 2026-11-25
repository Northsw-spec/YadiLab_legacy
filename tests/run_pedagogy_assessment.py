"""Run the P6 assessment against the native engine and actual Chromium."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys

from browser_icmp_lesson import ROOT, main as run_browser
from pedagogy_assessment import (
    Assessment, RETURN_CASES, check_insensitive_test, check_native_case,
    check_shared_symptom, check_unverified_repair,
)


COMMAND = "python3 tests/run_pedagogy_assessment.py"


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_assessment():
    assessment = Assessment()
    errors = []

    def run(name, check):
        try:
            with assessment.case(name) as signals:
                check(signals)
        except Exception:
            # The context captured the failure. Independent cases still run.
            pass

    for spec in RETURN_CASES:
        run(spec[0], lambda signals, case=spec: check_native_case(case, signals))
    run("shared-symptom", lambda _: check_shared_symptom())
    run("insensitive-test", check_insensitive_test)
    run("unverified-repair", check_unverified_repair)

    try:
        run_browser(assessment)
    except Exception as error:
        errors.append(f"{type(error).__name__}: {str(error)[:600]}")

    tracked_changes = git("status", "--porcelain", "--untracked-files=no")
    cases = assessment.results()
    return {
        "commit": git("rev-parse", "HEAD") or "NOT_VERIFIED",
        "tree": git("rev-parse", "HEAD^{tree}") or "NOT_VERIFIED",
        "tracked_changes": None if tracked_changes is None else bool(tracked_changes),
        "command": COMMAND,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "chromium": assessment.browser_version or "NOT_VERIFIED",
            "browser_transport": assessment.browser_transport or "NOT_VERIFIED",
        },
        "summary": assessment.summary(),
        "cases": cases,
        "harness_errors": errors,
        "coverage_limits": [
            "P1–P3: två guidade ICMP-fall. DHCP och övriga slumpade fall täcks av ordinarie regression.",
            "P4: fyra kort och uttryckliga påståenden. Körning av externa verktyg är NOT_VERIFIED.",
            "P5: två förberedda utfall och ett otillgängligt test per lektion.",
            "Teknisk korrekthet bedöms mot fixture och protokollfacit inom dessa fall.",
            "Undervisningsflödet granskas genom verklig Chromium och observerade grindar.",
        ],
        "human_learning_effect": "NOT_VERIFIED",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Skriv även JSON-rapporten till denna fil.")
    args = parser.parse_args(argv)
    if not __debug__:
        parser.error("Pythonoptimering får inte stänga av testassertioner.")
    report = run_assessment()
    document = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(document, encoding="utf-8")
    print(document, end="")
    summary = report["summary"]
    return int(bool(summary["FAIL"] or summary["NOT_RUN"] or report["harness_errors"]))


if __name__ == "__main__":
    sys.exit(main())
