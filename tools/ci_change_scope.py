#!/usr/bin/env python3
"""Fail-closed changed-file classifier for bounded documentation-only CI.

This controls *only* the runtime-intensive test matrix. Required architecture
guard and governance/supply-chain checks always execute. No network calls.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

SHA = re.compile(r"[a-f0-9]{40}\Z")
DOC_ROOT_FILES = frozenset({
    "AGENTS.md", "README.md",
    ".github/pull_request_template.md", ".github/copilot-instructions.md",
})


def is_document_path(path: str) -> bool:
    # Never treat licenses in vendor/, workflows, scripts, source or arbitrary
    # root Markdown names as safe based on extension alone.
    return (path in DOC_ROOT_FILES or
            (path.startswith("docs/") and path.endswith(".md")
             and ".." not in Path(path).parts))


def documentation_only(changes: list[tuple[str, str]]) -> bool:
    # A deletion, rename, mode-only, unknown or empty diff is not eligible.
    return bool(changes) and all(
        status in ("A", "M") and is_document_path(path)
        for status, path in changes
    )


def git(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), stderr=subprocess.PIPE)


def classify(base_sha: str, head: str = "HEAD") -> bool:
    if not SHA.fullmatch(base_sha):
        raise ValueError("PR base must be an exact 40-character SHA")
    raw = git("diff", "--name-status", "-z", "--no-renames",
              base_sha, head)
    records = raw.decode("utf-8").split("\0")
    if records[-1] == "":
        records.pop()
    if len(records) % 2:
        raise ValueError("unexpected git diff status output")
    changes = [(records[n], records[n + 1])
               for n in range(0, len(records), 2)]
    if not documentation_only(changes):
        return False
    for status, path in changes:
        # Mode-only changes must not qualify as documentation-only, including
        # executable-to-regular edits; both blobs must have regular-file mode.
        entry = git("ls-tree", "-z", head, "--", path)
        if not entry.startswith(b"100644 blob ") or entry.count(b"\0") != 1:
            return False
        if status == "M":
            old_entry = git("ls-tree", "-z", base_sha, "--", path)
            if not old_entry.startswith(b"100644 blob ") or old_entry.count(b"\0") != 1:
                return False
    return True


def main() -> int:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    output = os.environ.get("GITHUB_OUTPUT", "")
    if not output:
        print("Missing GITHUB_OUTPUT; refuse unverified scope", file=sys.stderr)
        return 1
    docs_only = False
    reason = "full acceptance by default"
    try:
        if event == "pull_request":
            base = os.environ.get("PR_BASE_SHA", "")
            docs_only = classify(base)
        elif event == "push" and os.environ.get("GITHUB_REF") == "refs/heads/main":
            base = git("rev-parse", "HEAD^").decode("ascii").strip()
            docs_only = classify(base)
        else:
            reason = "unexpected event/ref: full acceptance required"
    except (ValueError, OSError, subprocess.CalledProcessError, UnicodeError) as exc:
        # Never guess docs-only on missing history, malformed paths or failures.
        reason = "could not prove docs-only, using full acceptance: " + str(exc)
    with open(output, "a", encoding="utf-8") as stream:
        stream.write("docs_only=" + ("true" if docs_only else "false") + "\n")
    print("CI change scope:", "documentation-only" if docs_only else "full",
          "|", reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
