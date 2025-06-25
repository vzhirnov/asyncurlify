import shlex
import types

import pytest

from to_curl import to_curl


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
