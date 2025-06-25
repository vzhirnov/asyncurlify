import unittest
from asyncurlify import to_curl

class DummyRequestInfo:
    def __init__(self, method='GET', url='http://example.com', headers=None):
        self.method = method
        self.url = url
        self.headers = headers or {}

class DummyResponse:
    def __init__(self, method='GET', url='http://example.com', headers=None):
        self.request_info = DummyRequestInfo(method, url, headers)

class CurlifyTests(unittest.TestCase):
    def test_empty_body_included(self):
        resp = DummyResponse(headers={'User-Agent': 'test'})
        curl_cmd = to_curl(resp, body='')
        self.assertIn("-d ''", curl_cmd)

if __name__ == '__main__':
    unittest.main()
