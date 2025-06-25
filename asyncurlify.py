import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiohttp import ClientResponse

from shlex import quote


def to_curl(
    request: "ClientResponse",
    body: Any | None = None,
    compressed: bool = False,
    verify: bool = True,
) -> str:
    """Return a cURL command for the given request.

    Parameters
    ----------
    request : ClientResponse
        The HTTP response whose request information is to be converted. The
        value should be a :class:`aiohttp.ClientResponse` instance.
    body : optional
        Data to send as the request body. Dictionaries are encoded as JSON.
    compressed : bool, optional
        When ``True`` include the ``--compressed`` flag.
    verify : bool, optional
        When ``False`` add ``--insecure`` to disable TLS verification.

    Returns
    -------
    str
        The fully assembled cURL command string.
    """
    parts = [
        ("curl", None),
        ("-X", request.request_info.method),
    ]

    for k, v in sorted(request.request_info.headers.items()):
        parts.append(("-H", "{0}: {1}".format(k, v)))

    if body is not None:
        if isinstance(body, dict):
            body = json.dumps(body)
        elif isinstance(body, bytes):
            # fall back to replacing invalid bytes when decoding
            body = body.decode("utf-8", errors="replace")
        parts.append(("-d", body))

    if compressed:
        parts.append(("--compressed", None))

    if not verify:
        parts.append(("--insecure", None))

    parts.append((None, str(request.request_info.url)))

    flat_parts = []
    for k, v in parts:
        if k is not None:
            flat_parts.append(quote(k))
        if v is not None:
            flat_parts.append(quote(v))
    return " ".join(flat_parts)
