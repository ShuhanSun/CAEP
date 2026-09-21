from caep.redact import redact_json, redact_text


def test_redacts_sensitive_dict_keys():
    raw = {
        "env": {
            "OPENAI_API_KEY": "sk-secret",
            "NORMAL_VALUE": "keep",
            "CODEX_AUTH_JSON": "{secret}",
        },
        "nested": {"password": "p"},
    }
    cleaned = redact_json(raw)
    assert cleaned["env"]["OPENAI_API_KEY"] == "<redacted>"
    assert cleaned["env"]["CODEX_AUTH_JSON"] == "<redacted>"
    assert cleaned["env"]["NORMAL_VALUE"] == "keep"
    assert cleaned["nested"]["password"] == "<redacted>"


def test_redacts_assignment_strings_in_lists():
    raw = ["OPENAI_API_KEY=sk-secret", "FOO=bar"]
    cleaned = redact_json(raw)
    assert cleaned == ["OPENAI_API_KEY=<redacted>", "FOO=bar"]


def test_redacts_sensitive_text_patterns():
    raw = '\n'.join([
        'OPENAI_API_KEY=sk-secret',
        '"CODEX_AUTH_JSON": "{secret}"',
        'token: abc123',
        'normal=value',
    ])
    cleaned = redact_text(raw)
    assert 'OPENAI_API_KEY=<redacted>' in cleaned
    assert '"CODEX_AUTH_JSON": "<redacted>"' in cleaned
    assert 'token: <redacted>' in cleaned
    assert 'normal=value' in cleaned


def test_redacts_text_without_changing_surrounding_whitespace():
    cleaned = redact_text("token:  abc123  ")
    assert cleaned == "token:  <redacted>  "
