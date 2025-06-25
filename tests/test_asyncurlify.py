import sys
import types
import os
from types import SimpleNamespace

import pytest

# Provide a minimal stub for aiohttp so asyncurlify can be imported
aiohttp_stub = types.ModuleType('aiohttp')
class ClientResponse:  # pragma: no cover - minimal placeholder
    pass

aiohttp_stub.ClientResponse = ClientResponse
sys.modules.setdefault('aiohttp', aiohttp_stub)

# Ensure the repository root is on the import path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

import asyncurlify


class DummyResponse:
    def __init__(self, url='http://example.com', method='GET', headers=None):
        self.request_info = SimpleNamespace(
            url=url,
            method=method,
            headers=headers or {}
        )

@pytest.mark.feature('simple_get')
def test_simple_get():
    resp = DummyResponse(headers={'User-Agent': 'test'})
    expected = "curl -X GET -H 'User-Agent: test' http://example.com"
    assert asyncurlify.to_curl(resp) == expected

@pytest.mark.feature('json_body')
def test_json_body():
    resp = DummyResponse(method='POST', headers={'content-type': 'application/json'})
    expected = "curl -X POST -H 'content-type: application/json' -d '{\"a\": 1}' http://example.com"
    assert asyncurlify.to_curl(resp, body={'a': 1}) == expected

@pytest.mark.feature('compressed_flag')
def test_compressed_flag():
    resp = DummyResponse()
    expected = "curl -X GET --compressed http://example.com"
    assert asyncurlify.to_curl(resp, compressed=True) == expected

@pytest.mark.feature('verify_false')
def test_verify_false():
    resp = DummyResponse()
    expected = "curl -X GET --insecure http://example.com"
    assert asyncurlify.to_curl(resp, verify=False) == expected
