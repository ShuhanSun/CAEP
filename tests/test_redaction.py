from caep.redact import redact_json


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
