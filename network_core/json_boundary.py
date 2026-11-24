"""Strict UTF-8 JSON input boundary for untrusted HTTP and project files.

The canonical project validator checks field semantics after decoding. A JSON
decoder must first reject ambiguous duplicate members and malformed Unicode,
otherwise facts can be silently lost before validation ever sees them.
"""
from __future__ import annotations

import json
import math

from .model import ProjectValidationError

MAX_JSON_DEPTH = 64  # Canonical projects and import evidence require far less nesting.


def decode_json_document(data: bytes, *, context: str) -> object:
    """Decode one bounded UTF-8 document; reject duplicate keys and invalid text."""
    if type(data) is not bytes:
        raise ProjectValidationError(f"{context}: expected UTF-8 JSON bytes")

    def unique_members(pairs: list[tuple[str, object]]) -> dict:
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ProjectValidationError(f"{context}: duplicate JSON member {key!r}")
            obj[key] = value
        return obj

    def unsupported_constant(value: str) -> object:
        raise ProjectValidationError(f"{context}: non-finite JSON constant {value!r}")

    try:
        document = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=unique_members,
            parse_constant=unsupported_constant,
        )
    except ProjectValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise ProjectValidationError(f"{context}: invalid JSON") from None

    # json.loads can decode lone surrogate escapes and overflowed exponents.
    # An iterative traversal avoids a second recursion-depth failure.
    pending = [(document, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > MAX_JSON_DEPTH:
            raise ProjectValidationError(
                f"{context}: JSON nesting exceeds {MAX_JSON_DEPTH} levels")
        if type(current) is str:
            try:
                current.encode("utf-8")
            except UnicodeEncodeError:
                raise ProjectValidationError(
                    f"{context}: invalid Unicode surrogate in JSON text") from None
        elif type(current) is dict:
            pending.extend((item, depth + 1) for item in current.keys())
            pending.extend((item, depth + 1) for item in current.values())
        elif type(current) is list:
            pending.extend((item, depth + 1) for item in current)
        elif type(current) is float and not math.isfinite(current):
            raise ProjectValidationError(f"{context}: non-finite JSON number")
    return document
