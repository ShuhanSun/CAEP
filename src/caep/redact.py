from __future__ import annotations

import re
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(api[_-]?key|token|secret|password|auth[_-]?json|credential)",
    re.IGNORECASE,
)
_ASSIGNMENT = re.compile(r"^\s*([^=]+?)\s*=\s*(.*)$", re.DOTALL)
_KEY_VALUE = re.compile(
    r'(?im)((?:^|[{\[,])\s*)(["\']?)([A-Za-z0-9_.-]*'
    r"(?:api[_-]?key|token|secret|password|auth[_-]?json|credential)"
    r'[A-Za-z0-9_.-]*)(\2)(\s*[:=]\s*)((?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|.*?))(?=(?:\s*[,}\]])|$)'
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

    def replace_key_value(match: re.Match[str]) -> str:
        key = match.group(3)
        if _is_sensitive_key(key):
            value = match.group(6)
            leading_len = len(value) - len(value.lstrip())
            trailing_len = len(value) - len(value.rstrip())
            leading = value[:leading_len]
            trailing = value[len(value) - trailing_len:] if trailing_len else ""
            core_end = len(value) - trailing_len if trailing_len else len(value)
            core = value[leading_len:core_end]
            replacement = "<redacted>"
            if len(core) >= 2 and core[0] in {"'", '"'} and core[-1] == core[0]:
                replacement = f"{core[0]}<redacted>{core[0]}"
            return f"{match.group(1)}{match.group(2)}{key}{match.group(4)}{match.group(5)}{leading}{replacement}{trailing}"
        return match.group(0)

    return _KEY_VALUE.sub(replace_key_value, text)
