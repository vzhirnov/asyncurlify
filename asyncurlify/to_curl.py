"""
Light-weight helper that turns an *aiohttp* request into a POSIX-shell-ready
`curl …` one-liner.  The implementation is intentionally self-contained and
does not require `aiohttp` at runtime (import only for static type checkers).
"""
from __future__ import annotations  # → PEP 563 for Py 3.8/3.9

import json
from shlex import quote
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from aiohttp import ClientResponse  # noqa: F401

__all__ = ["to_curl"]


def _needs_compressed_flag(hdrs: list[tuple[str, str]]) -> bool:
    """Return *True* if original request explicitly asked for gz/deflate/brotli."""
    for name, value in hdrs:
        if name.lower() == "accept-encoding" and any(
            enc in value.lower() for enc in ("gzip", "deflate", "br")
        ):
            return True
    return False


def to_curl(
    response: "ClientResponse",
    body: Any | None = None,
    *,
    compressed: bool | None = None,
    verify: bool = True,
    redact_headers: tuple[str, ...] = ("Authorization", "X-Api-Key", "Cookie"),
) -> str:
    """
    Build a POSIX-shell command that reproduces the HTTP request behind
    *response*.

    Parameters
    ----------
    response
        ``aiohttp.ClientResponse`` obtained from *aiohttp* call.
    body
        Payload override. ``dict`` → JSON; ``bytes`` → UTF-8 (with fallback).
    compressed
        • ``True``  — always add ``--compressed`` flag.
        • ``False`` — never add it.
        • ``None``  — automatically add if original request had
          ``Accept-Encoding: gzip/deflate/br`` header (default).
    verify
        ``False`` ⇒ add ``--insecure`` flag.
    redact_headers
        Headers whose values will be replaced with ``<redacted>`` string.

    Notes
    -----
    * ``Content-Length`` header is not copied — let curl compute it.
    * Header order is preserved, which allows correct reproduction of
      HMAC-signed requests (AWS Sig v4, etc.).
    * If method is ``GET``/``HEAD`` and ``body`` is provided, ``-G`` flag is added.
    """
    rq = response.request_info
    method = rq.method.upper()
    hdrs = list(rq.headers.items())  # CIMultiDict preserves order

    parts: list[tuple[str | None, str | None]] = [
        ("curl", None),
        ("-X", method),
    ]

    # -------- headers --------
    for name, value in hdrs:
        if name.lower() == "content-length":
            continue  # length mismatch is more dangerous than missing header
        if name in redact_headers:
            value = "<redacted>"
        parts.append(("-H", f"{name}: {value}"))

    # -------- body / query --------
    if body is not None:
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(body, bytes):
            try:
                body = body.decode("utf-8")
            except UnicodeDecodeError:
                body = body.decode("utf-8", errors="replace")

        if method in ("GET", "HEAD"):
            parts.append(("-G", None))
        parts.append(("-d", body))

    # -------- flags --------
    if compressed is True or (
        compressed is None and _needs_compressed_flag(hdrs)
    ):
        parts.append(("--compressed", None))

    if not verify:
        parts.append(("--insecure", None))

    # -------- URL --------
    parts.append((None, str(rq.url)))

    # -------- flatten & quote --------
    flat: list[str] = []
    for k, v in parts:
        if k is not None:
            flat.append(quote(k))
        if v is not None:
            flat.append(quote(v))
    return " ".join(flat)
  
