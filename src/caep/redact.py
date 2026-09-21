from __future__ import annotations

import re
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(api[_-]?key|token|secret|password|auth[_-]?json|credential)",
    re.IGNORECASE,
)
_ASSIGNMENT = re.compile(r"^\\s*([^=]+?)\\s*=\\s*(.*)$", re.DOTALL)


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
