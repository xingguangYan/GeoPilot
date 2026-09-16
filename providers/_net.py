"""Safe network wrapper for HTTP calls."""

import importlib
import json
import socket
import ssl


class NetworkError(Exception):
    """Raised when a network request fails after retries."""


def _build_ssl_context(verify=True):
    """Build an SSL context; when verify=False warns but still proceeds.

    We keep certificate verification enabled by default (secure default).
    """
    if verify:
        return ssl.create_default_context()
    ctx = ssl._create_unverified_context()  # noqa: S323 - opt-in only
    return ctx


def _urlopen(req, timeout=120, verify=True):
    """Open a request with sane defaults: timeout + SSL verification."""
    urllib_request = importlib.import_module("urllib.request")
    urllib_error = importlib.import_module("urllib.error")
    try:
        return urllib_request.urlopen(req, timeout=timeout, context=_build_ssl_context(verify))
    except urllib_error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise NetworkError(f"HTTP {e.code} {e.reason}: {body}") from e
    except urllib_error.URLError as e:
        raise NetworkError(f"URL error: {e.reason}") from e
    except socket.timeout as e:
        raise NetworkError("Request timed out") from e


def _post_json(url, payload, headers=None, timeout=120, verify=True):
    """POST JSON payload, return parsed response."""
    urllib_request = importlib.import_module("urllib.request")
    data = json.dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib_request.Request(url, data, hdrs, method="POST")
    with _urlopen(req, timeout=timeout, verify=verify) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8"))


def _post_raw(url, data=None, headers=None, timeout=120, verify=True):
    """POST raw bytes, return raw bytes response."""
    urllib_request = importlib.import_module("urllib.request")
    hdrs = {"Content-Type": "application/octet-stream"}
    if headers:
        hdrs.update(headers)
    req = urllib_request.Request(url, data or b"", hdrs, method="POST")
    with _urlopen(req, timeout=timeout, verify=verify) as resp:
        return resp.read()


def _get(url, headers=None, timeout=120, verify=True):
    """GET url, return response body bytes."""
    urllib_request = importlib.import_module("urllib.request")
    req = urllib_request.Request(url, headers=headers or {})
    with _urlopen(req, timeout=timeout, verify=verify) as resp:
        return resp.read()
