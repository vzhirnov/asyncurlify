import aiohttp
import json

from shlex import quote


def to_curl(request: aiohttp.ClientResponse, body=None, compressed=False, verify=True):

    parts = [
        ("curl", None),
        ("-X", request.request_info.method),
    ]

    for k, v in sorted(request.request_info.headers.items()):
        parts += [("-H", "{0}: {1}".format(k, v))]

    if body:
        if isinstance(body, dict):
            body = json.dumps(body).encode("utf-8")
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        parts += [("-d", body)]

    if compressed:
        parts += [("--compressed", None)]

    if not verify:
        parts += [("--insecure", None)]

    parts += [(None, str(request.request_info.url))]

    flat_parts = []
    for k, v in parts:
        if k:
            flat_parts.append(quote(k))
        if v:
            flat_parts.append(quote(v))
    return " ".join(flat_parts)
