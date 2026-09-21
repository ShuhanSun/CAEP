from __future__ import annotations

import re
from typing import Any


_KEY_VALUE_START = re.compile(
    r"""(?ix)
    (?<![A-Za-z0-9_.-])
    (?P<quote>["']?)
    (?P<key>[A-Za-z_][A-Za-z0-9_.-]*)
    (?P=quote)
    (?P<sep>\s*[:=]\s*)
    """
)


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")


def _is_sensitive_key(key: str) -> bool:
    """Return True for credential-bearing keys, not token-usage metrics."""
    normalized = _normalized_key(key)
    if not normalized:
        return False

    # Evaluation evidence frequently contains token counters. These must survive
    # sanitization even though their names contain the word "token".
    if (
        normalized == "tokens"
        or normalized.endswith("_tokens")
        or normalized.startswith("tokens_")
        or normalized == "token_count"
        or normalized.endswith("_token_count")
        or normalized.startswith("token_count_")
        or normalized in {"token_usage", "token_usage_count"}
    ):
        return False

    if normalized in {
        "token",
        "secret",
        "password",
        "credential",
        "credentials",
        "api_key",
        "apikey",
        "auth_json",
        "authorization",
        "client_secret",
        "access_token",
        "refresh_token",
        "id_token",
        "session_token",
        "bearer_token",
        "private_key",
    }:
        return True

    if normalized.endswith(
        (
            "_api_key",
            "_apikey",
            "_secret",
            "_password",
            "_credential",
            "_credentials",
            "_auth_json",
            "_authorization",
            "_client_secret",
            "_access_token",
            "_refresh_token",
            "_id_token",
            "_session_token",
            "_bearer_token",
            "_private_key",
        )
    ):
        return True

    # Catch provider-specific credentials such as GITHUB_TOKEN while still
    # excluding *_tokens and *_token_count above.
    return normalized.endswith("_token")


def _quoted_value_end(text: str, start: int) -> int:
    quote = text[start]
    i = start + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    return len(text)


def _balanced_value_end(text: str, start: int) -> int:
    pairs = {"[": "]", "{": "}"}
    stack = [pairs[text[start]]]
    quote: str | None = None
    i = start + 1

    while i < len(text):
        ch = text[i]
        if quote is not None:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue

        if ch in {'"', "'"}:
            quote = ch
            i += 1
            continue
        if ch in pairs:
            stack.append(pairs[ch])
            i += 1
            continue
        if ch == stack[-1]:
            stack.pop()
            i += 1
            if not stack:
                return i
            continue
        i += 1

    # Fail closed for malformed structured values: redact through EOF rather
    # than risking a partial credential leak.
    return len(text)


def _scalar_value_end(text: str, start: int, *, allow_spaces: bool = False) -> int:
    i = start
    while i < len(text):
        ch = text[i]
        if ch in "\r\n,;}])\"'":
            break
        if ch in " \t":
            if not allow_spaces:
                break
            next_nonspace = i
            while next_nonspace < len(text) and text[next_nonspace] in " \t":
                next_nonspace += 1
            # Keep spaces that are part of a credential value (for example
            # "Authorization: Bearer ..."), but stop before the next key/value
            # field when parsing a log line.
            if _KEY_VALUE_START.match(text, next_nonspace):
                break
        i += 1
    return i


def redact_text(text: str) -> str:
    """Redact credential-bearing key/value pairs from arbitrary text evidence.

    The scanner accepts ordinary log prefixes, preserves quoted scalar syntax,
    and replaces structured secret values with a JSON-compatible string marker.
    """
    output: list[str] = []
    pos = 0

    while True:
        match = _KEY_VALUE_START.search(text, pos)
        if match is None:
            output.append(text[pos:])
            break

        output.append(text[pos:match.end()])
        if not _is_sensitive_key(match.group("key")):
            pos = match.end()
            continue

        start = match.end()
        if start >= len(text):
            output.append("<redacted>")
            pos = start
            continue

        first = text[start]
        if first in {'"', "'"}:
            end = _quoted_value_end(text, start)
            if end > start + 1 and text[end - 1] == first:
                replacement = f"{first}<redacted>{first}"
            else:
                replacement = f"{first}<redacted>"
        elif first in "[{":
            end = _balanced_value_end(text, start)
            replacement = '"<redacted>"'
        else:
            normalized_key = _normalized_key(match.group("key"))
            end = _scalar_value_end(
                text,
                start,
                allow_spaces=(
                    normalized_key == "authorization"
                    or normalized_key.endswith("_authorization")
                ),
            )
            replacement = "<redacted>"

        output.append(replacement)
        pos = end

    return "".join(output)


def redact_json(value: Any) -> Any:
    """Recursively redact credential-bearing fields and strings."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                out[key] = "<redacted>"
            else:
                out[key] = redact_json(item)
        return out
    if isinstance(value, list):
        return [redact_json(item) for item in value]
    if isinstance(value, str):
        # Trajectories can embed shell commands and verifier output inside JSON
        # strings, so sanitize those strings as text too.
        return redact_text(value)
    return value
