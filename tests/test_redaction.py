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


def test_redacts_inline_structured_text_without_breaking_delimiters():
    cleaned = redact_text('prefix {"token":"abc","safe":"ok"} suffix')
    assert cleaned == 'prefix {"token":"<redacted>","safe":"ok"} suffix'



def test_preserves_token_usage_metrics():
    raw = {
        "total_prompt_tokens": 100,
        "total_completion_tokens": 20,
        "total_cached_tokens": 5,
        "token_count": 125,
        "github_token": "gh-secret",
    }
    cleaned = redact_json(raw)
    assert cleaned["total_prompt_tokens"] == 100
    assert cleaned["total_completion_tokens"] == 20
    assert cleaned["total_cached_tokens"] == 5
    assert cleaned["token_count"] == 125
    assert cleaned["github_token"] == "<redacted>"


def test_redacts_prefixed_log_credentials():
    raw = "\n".join([
        "INFO token=abc",
        "2026-09-21 TOKEN=def",
        "export OPENAI_API_KEY=ghi",
    ])
    cleaned = redact_text(raw)
    assert "INFO token=<redacted>" in cleaned
    assert "2026-09-21 TOKEN=<redacted>" in cleaned
    assert "export OPENAI_API_KEY=<redacted>" in cleaned


def test_redacts_nested_structured_values_without_breaking_json():
    array_text = '{"token":["a","b"],"safe":"ok"}'
    object_text = '{"token":{"nested":["a","b"]},"safe":"ok"}'

    cleaned_array = redact_text(array_text)
    cleaned_object = redact_text(object_text)

    assert cleaned_array == '{"token":"<redacted>","safe":"ok"}'
    assert cleaned_object == '{"token":"<redacted>","safe":"ok"}'


def test_redacts_credentials_embedded_in_json_strings():
    raw = {
        "message": "INFO token=abc",
        "command": "export OPENAI_API_KEY=secret",
        "usage": "total_prompt_tokens=100",
    }
    cleaned = redact_json(raw)
    assert cleaned["message"] == "INFO token=<redacted>"
    assert cleaned["command"] == "export OPENAI_API_KEY=<redacted>"
    assert cleaned["usage"] == "total_prompt_tokens=100"



def test_redacts_authorization_bearer_value():
    cleaned = redact_text("Authorization: Bearer abc.def.ghi")
    assert cleaned == "Authorization: <redacted>"


def test_authorization_redaction_stops_before_next_field():
    cleaned = redact_text("Authorization: Bearer abc next=value")
    assert cleaned == "Authorization: <redacted> next=value"
