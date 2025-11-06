import shlex
import types

import pytest

from asyncurlify import to_curl


def _dummy_response(method="GET", url="https://example.com", headers=None):
    """Create a minimal stand-in for aiohttp.ClientResponse."""
    if headers is None:
        headers = {}
    request_info = types.SimpleNamespace(method=method, url=url, headers=headers)
    return types.SimpleNamespace(request_info=request_info)


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_basic_command_contains_core_parts(method):
    resp = _dummy_response(method=method)
    cmd = to_curl(resp)
    parts = shlex.split(cmd)

    assert parts[0] == "curl"
    assert "-X" in parts and method in parts
    assert "https://example.com" in parts


def test_json_body_serialised():
    data = {"ключ": "значение"}  # non-ASCII to verify ensure_ascii=False
    resp = _dummy_response(method="POST")
    cmd = to_curl(resp, body=data)
    assert '{"ключ":"значение"}' in cmd  # compact, unicode-safe JSON
    assert "-d" in shlex.split(cmd)


def test_get_with_body_adds_dash_G():
    resp = _dummy_response(method="GET")
    cmd = to_curl(resp, body="a=1")
    parts = shlex.split(cmd)
    assert "-G" in parts  # ensures body turns into query string


def test_content_length_filtered_out():
    headers = {"Content-Length": "999"}
    resp = _dummy_response(method="POST", headers=headers)
    cmd = to_curl(resp, body="x")
    assert "Content-Length" not in cmd


def test_authorization_redacted():
    headers = {"Authorization": "Bearer 123"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    assert "Bearer 123" not in cmd
    assert "<redacted>" in cmd


def test_compressed_flag_auto():
    headers = {"Accept-Encoding": "gzip, deflate"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)  # compressed=None by default
    assert "--compressed" in shlex.split(cmd)


def test_insecure_flag():
    resp = _dummy_response()
    cmd = to_curl(resp, verify=False)
    assert "--insecure" in shlex.split(cmd)


def test_head_method_with_body_adds_dash_G():
    """HEAD method with body should add -G flag, like GET."""
    resp = _dummy_response(method="HEAD")
    cmd = to_curl(resp, body="test=1")
    parts = shlex.split(cmd)
    assert "-G" in parts
    assert "HEAD" in parts


def test_bytes_body_decoded_as_utf8():
    """Bytes body should be decoded to UTF-8 string."""
    body = "тест данные".encode("utf-8")
    resp = _dummy_response(method="POST")
    cmd = to_curl(resp, body=body)
    assert "тест данные" in cmd
    assert "-d" in shlex.split(cmd)


def test_bytes_body_with_decode_error():
    """Invalid UTF-8 bytes should use replacement characters."""
    body = b"\xff\xfe invalid utf-8"
    resp = _dummy_response(method="POST")
    cmd = to_curl(resp, body=body)
    # Should not raise exception, uses errors='replace'
    assert "-d" in shlex.split(cmd)
    assert "invalid utf-8" in cmd


def test_string_body():
    """Plain string body should be passed through."""
    resp = _dummy_response(method="POST")
    cmd = to_curl(resp, body="plain text data")
    assert "plain text data" in cmd
    assert "-d" in shlex.split(cmd)


def test_compressed_flag_explicit_true():
    """compressed=True should always add --compressed."""
    resp = _dummy_response()  # no Accept-Encoding header
    cmd = to_curl(resp, compressed=True)
    assert "--compressed" in shlex.split(cmd)


def test_compressed_flag_explicit_false():
    """compressed=False should never add --compressed, even with Accept-Encoding."""
    headers = {"Accept-Encoding": "gzip"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp, compressed=False)
    assert "--compressed" not in shlex.split(cmd)


def test_compressed_flag_brotli():
    """Accept-Encoding with 'br' (brotli) should trigger --compressed."""
    headers = {"Accept-Encoding": "br"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    assert "--compressed" in shlex.split(cmd)


def test_compressed_flag_case_insensitive():
    """Accept-Encoding header check should be case-insensitive."""
    headers = {"Accept-Encoding": "GZIP"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    assert "--compressed" in shlex.split(cmd)


def test_x_api_key_redacted():
    """X-Api-Key header should be redacted by default."""
    headers = {"X-Api-Key": "secret-key-123"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    assert "secret-key-123" not in cmd
    assert "<redacted>" in cmd


def test_cookie_redacted():
    """Cookie header should be redacted by default."""
    headers = {"Cookie": "session=abc123"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    assert "abc123" not in cmd
    assert "<redacted>" in cmd


def test_custom_redact_headers():
    """Should allow custom redaction list."""
    headers = {"Authorization": "Bearer token", "X-Custom": "secret"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp, redact_headers=("X-Custom",))
    # Authorization should NOT be redacted now
    assert "Bearer token" in cmd
    # X-Custom should be redacted
    assert "secret" not in cmd
    assert "<redacted>" in cmd


def test_multiple_headers_preserve_order():
    """Multiple headers should preserve their order."""
    headers = {
        "X-First": "1",
        "X-Second": "2",
        "X-Third": "3",
    }
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    # Find positions of headers in command
    pos_first = cmd.find("X-First: 1")
    pos_second = cmd.find("X-Second: 2")
    pos_third = cmd.find("X-Third: 3")
    # All should be present
    assert pos_first != -1
    assert pos_second != -1
    assert pos_third != -1
    # Order should be preserved
    assert pos_first < pos_second < pos_third


def test_special_characters_in_url():
    """URL with special characters should be properly quoted."""
    url = "https://example.com/path?query=hello world&foo=bar"
    resp = _dummy_response(url=url)
    cmd = to_curl(resp)
    # The command should be parseable
    parts = shlex.split(cmd)
    assert "curl" in parts
    # URL should be in the command (quoted or as single argument)
    assert url in parts or any(url in p for p in parts)


def test_special_characters_in_headers():
    """Headers with special characters should be properly quoted."""
    headers = {"X-Custom": "value with spaces and 'quotes'"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp)
    # Should not raise exception and should be parseable
    parts = shlex.split(cmd)
    assert "curl" in parts
    # Header should be present in some form
    assert "X-Custom" in cmd


def test_empty_headers():
    """Request with no custom headers should work."""
    resp = _dummy_response(headers={})
    cmd = to_curl(resp)
    parts = shlex.split(cmd)
    assert parts[0] == "curl"
    assert "https://example.com" in parts


def test_content_length_case_insensitive():
    """Content-Length filtering should be case-insensitive."""
    headers = {"content-length": "100", "Content-Length": "200"}
    resp = _dummy_response(headers=headers)
    cmd = to_curl(resp, body="test")
    # Both variations should be filtered
    assert "Content-Length" not in cmd and "content-length" not in cmd
