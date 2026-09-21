from __future__ import annotations

import re
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(api[_-]?key|token|secret|password|auth[_-]?json|credential)",
    re.IGNORECASE,
)
_ASSIGNMENT = re.compile(r"^\s*([^=]+?)\s*=\s*(.*)$", re.DOTALL)
_JSON_PAIR = re.compile(
    r'(["\'])((?:[^\\\n]|\\.)*?)\1(\s*:\s*)(["\'])(.*?)\4',
    re.IGNORECASE | re.DOTALL,
)
_KEY_VALUE = re.compile(
    r"(?im)^(\s*)([A-Za-z0-9_.-]*"
    r"(?:api[_-]?key|token|secret|password|auth[_-]?json|credential)"
    r"[A-Za-z0-9_.-]*)(\s*[:=]\s*)(.+)$"
)


def _is_sensitive_key(key: str) -> bool:
    return bool(_SENSITIVE_KEY.search(key))


def redact_json(value: Any) -> Any:
    """Recursively redact common credential-bearing fields."""
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
        match = _ASSIGNMENT.match(value)
        if match and _is_sensitive_key(match.group(1)):
            return f"{match.group(1)}=<redacted>"
        return value
    return value


def redact_text(text: str) -> str:
    """Redact common credential-bearing key/value patterns from text evidence."""

    def replace_json_pair(match: re.Match[str]) -> str:
        key = match.group(2)
        if _is_sensitive_key(key):
            return f'{match.group(1)}{key}{match.group(1)}{match.group(3)}{match.group(4)}<redacted>{match.group(4)}'
        return match.group(0)

    def replace_key_value(match: re.Match[str]) -> str:
        key = match.group(2)
        if _is_sensitive_key(key):
            return f"{match.group(1)}{key}{match.group(3)}<redacted>"
        return match.group(0)

    text = _JSON_PAIR.sub(replace_json_pair, text)
    return _KEY_VALUE.sub(replace_key_value, text)
