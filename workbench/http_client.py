"""A bounded HTTP client. The only thing in the workbench that opens sockets.

Why not `requests`, or even `urllib.request`
--------------------------------------------
Because the controls this workbench needs are exactly the ones a general-purpose
client treats as conveniences:

* **Connect to the address that was vetted, not the name that was typed.** The
  scope guard resolves the host and clears the address; this client then
  connects to *that address* with the original `Host` header. If it re-resolved
  the name, a DNS answer that changes between the check and the connection would
  move the request to a host nobody authorised. `urllib` re-resolves.
* **Redirects are re-checked, not followed.** Every hop goes back through the
  scope gate as a new request. A redirect to an out-of-scope host is a refusal
  with the chain recorded, which is also the finding worth having.
* **Bodies are bounded while they are read.** A 4 GiB response is a denial of
  service against the operator, so the cap is enforced on the socket read, not
  after buffering.
* **Failures are data.** A timeout, a refused connection, a bad certificate and
  a 500 are all recorded results with a reason — never an exception that loses
  the evidence of what happened.

Only `http` and `https` are reachable, the scheme is checked twice (here and in
the scope gate), and there is no code path that sends a request without a
`ScopeGuard` decision.
"""

from __future__ import annotations

import http.client
import socket
import ssl
import time
import urllib.parse

from .scope import ScopeError, require

REDACTED = "[redacted]"

# Headers whose values never reach a record, a log or a report.
SENSITIVE_HEADERS = (
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "api-key", "x-auth-token", "x-amz-security-token",
)

DEFAULT_UA = "BLACKHEART-workbench/1.0 (+authorized assessment; see workbench/AUTHORIZED-USE.md)"


# Cookie attributes are configuration, not secrets: whether a session cookie
# carries HttpOnly is exactly the kind of thing a review needs to see, and it is
# not something an attacker learns anything from. Values are removed; attributes
# are kept.
COOKIE_ATTRIBUTES = ("path", "domain", "expires", "max-age", "samesite",
                     "priority", "partitioned")


def _redact_cookie_header(value):
    """`Cookie: a=1; b=2` becomes `Cookie: a=[redacted]; b=[redacted]`."""
    parts = []
    for segment in str(value).split(";"):
        stripped = segment.strip()
        if not stripped:
            continue
        if "=" in stripped:
            name = stripped.split("=", 1)[0].strip()
            parts.append(f"{name}={REDACTED}")
        else:
            parts.append(stripped)
    return "; ".join(parts) if parts else REDACTED


def _redact_set_cookie(value):
    """Keep the cookie name and its attributes; remove the value it carries.

    Replacing the whole line with `[redacted]` was the first thing this code did
    and it made the response unusable as evidence: the flags are the part a
    reviewer reads. The value is the part that must not be stored.
    """
    parts = []
    for index, segment in enumerate(str(value).split(";")):
        stripped = segment.strip()
        if not stripped:
            continue
        if "=" not in stripped:
            parts.append(stripped)                      # HttpOnly, Secure, ...
            continue
        name, _, attr_value = stripped.partition("=")
        name = name.strip()
        if index == 0 or name.lower() not in COOKIE_ATTRIBUTES:
            parts.append(f"{name}={REDACTED}")
        else:
            parts.append(f"{name}={attr_value.strip()}")
    return "; ".join(parts) if parts else REDACTED


def is_redacted(value):
    """True when a header value carries the marker, wholly or in part."""
    return REDACTED in str(value)


def redact_headers(headers):
    """Case-insensitive redaction, applied wherever headers are recorded.

    The point is not tidiness: an exchange written to disk with a live
    `Authorization` header turns the evidence directory into a credential store,
    and evidence gets copied, pasted into reports and attached to tickets.

    Cookie headers are redacted value-by-value rather than line-by-line, so the
    record still says which flags were set without storing what the cookie held.
    """
    out = {}
    for name, value in headers.items():
        lowered = name.lower()
        if lowered == "set-cookie":
            out[name] = _redact_set_cookie(value)
        elif lowered == "cookie":
            out[name] = _redact_cookie_header(value)
        elif lowered in SENSITIVE_HEADERS:
            out[name] = REDACTED
        else:
            out[name] = value
    return out


def split_headers(request_headers):
    """Separate a header mapping into names and values, as git-style lists."""
    return list(request_headers or {})


class TLSInfo:
    """What can be learned about the connection without touching the private key."""

    def __init__(self, sock=None, version=None, cipher=None, cert=None):
        self.version = version
        self.cipher = cipher
        self.cert = cert or {}
        if sock is not None:
            try:
                self.version = sock.version()
            except Exception:
                pass
            try:
                c = sock.cipher()
                self.cipher = f"{c[0]}/{c[1]}/{c[2]}" if c else None
            except Exception:
                pass
            try:
                self.cert = sock.getpeercert() or {}
            except Exception:
                self.cert = {}

    def as_dict(self):
        cert = self.cert or {}
        subject = ", ".join(f"{k}={v}" for rdn in cert.get("subject", ()) for k, v in rdn)
        issuer = ", ".join(f"{k}={v}" for rdn in cert.get("issuer", ()) for k, v in rdn)
        return {
            "version": self.version,
            "cipher": self.cipher,
            "subject": subject,
            "issuer": issuer,
            "not_after": cert.get("notAfter"),
            "san": [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"],
        }


class Response:
    """One HTTP response, with the body already bounded."""

    def __init__(self):
        self.status = None
        self.reason = ""
        self.headers = {}
        self.body = b""
        self.truncated = False
        self.elapsed_ms = 0
        self.tls = None
        self.error = None
        self.http_version = ""
        self.address = ""

    @property
    def content_type(self):
        return (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()

    @property
    def content_length_header(self):
        raw = self.headers.get("Content-Length")
        try:
            return int(raw) if raw is not None else None
        except ValueError:
            return None

    @property
    def text(self, limit=200_000):
        """Decoded body text, never raising on undecodable bytes."""
        try:
            return self.body[:limit].decode("utf-8", errors="replace")
        except Exception:
            return ""

    def as_dict(self, include_body=True, body_limit=None):
        data = {
            "status": self.status,
            "reason": self.reason,
            "http_version": self.http_version,
            "headers": dict(self.headers),
            "content_type": self.content_type,
            "bytes": len(self.body),
            "content_length_header": self.content_length_header,
            "truncated": self.truncated,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
            "tls": self.tls.as_dict() if self.tls else None,
        }
        if include_body:
            body = self.body if body_limit is None else self.body[:body_limit]
            data["body_text"] = body.decode("utf-8", errors="replace")
        return data


class Exchange:
    """A request/response pair plus its provenance: what was sent, to what, when.

    `record()` produces the persisted form and is the only thing that should be
    written to disk or handed to a report. `redacted` marks that it already
    passed through `redact_headers`.
    """

    def __init__(self, url, method, request_headers, request_body=b"",
                 scope_decision=None, note=""):
        self.url = url
        self.method = method
        self.request_headers = dict(request_headers or {})
        self.request_body = request_body or b""
        self.response = None
        self.redirect_chain = []
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.scope_decision = scope_decision.as_dict() if scope_decision else None
        self.note = note
        self.redacted = False

    def record(self, include_body=True, body_limit=100_000, secrets=()):
        """The persisted form. Redaction happens here, once, for everything.

        Headers are redacted by name. `secrets` covers the other direction: a
        server that echoes an `Authorization` header into its response body puts
        the credential in the evidence, and a value the caller knows to be a
        credential is replaced wherever it appears. Bodies are otherwise stored
        as received, because a body edited beyond recognition is not evidence.
        """
        if not self.redacted:
            self.request_headers = redact_headers(self.request_headers)
            self.redacted = True
        parsed = urllib.parse.urlsplit(self.url)
        data = {
            "timestamp": self.timestamp,
            "method": self.method,
            "url": self.url,
            "scheme": parsed.scheme,
            "host": parsed.hostname,
            "port": parsed.port,
            "path": parsed.path,
            "query": parsed.query,
            "request_headers": dict(self.request_headers),
            "request_body_bytes": len(self.request_body),
            "redirect_chain": list(self.redirect_chain),
            "scope_decision": self.scope_decision,
            "note": self.note,
        }
        data["request_body"] = _scrub(
            self.request_body.decode("utf-8", errors="replace")[:body_limit], secrets)
        if self.response is not None:
            resp = self.response.as_dict(include_body=include_body, body_limit=body_limit)
            resp["headers"] = redact_headers(resp["headers"])
            if include_body and resp.get("body_text"):
                resp["body_text"] = _scrub(resp["body_text"], secrets)
            data["response"] = resp
        else:
            data["response"] = None
        return data


def _scrub(text, secrets):
    """Replace known credential values with the redaction marker."""
    for value in secrets or ():
        if value and len(str(value)) >= 4:
            text = text.replace(str(value), REDACTED)
    return text


def _connect(scheme, host, port, address, timeout, allow_private):
    """Open a socket to a vetted address, with TLS when the scheme is https.

    `server_hostname` is the *name*, not the address, so certificate
    verification still checks the name that was authorised even though the
    connection is pinned to an address.
    """
    sock = socket.create_connection((address, port), timeout=timeout)
    if scheme == "https":
        context = ssl.create_default_context()
        if allow_private:
            # Only reachable when the scope authorises non-public addresses; a
            # private CA is normal on an internal engagement.
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context.wrap_socket(sock, server_hostname=host), None
    return sock, None


def request(guard, url, method="GET", *, headers=None, body=None, timeout=None,
            max_bytes=None, max_redirects=None, follow_redirects=True,
            confirm_write=False, record_body_limit=100_000, note="",
            include_body=True):
    """Send one request (plus any in-scope redirects). Never raises for HTTP errors.

    Returns an `Exchange`. Raises `ScopeError` — and only `ScopeError` — when the
    scope gate refuses, because a refusal is a decision the caller must see
    rather than a transport failure to log and continue past.
    """
    scope = guard.scope
    timeout = float(timeout if timeout is not None else scope.timeout_s)
    max_bytes = int(max_bytes if max_bytes is not None else scope.max_response_bytes)
    max_redirects = int(max_redirects if max_redirects is not None else scope.max_redirects)

    headers = dict(headers or {})
    headers.setdefault("User-Agent", DEFAULT_UA)
    headers.setdefault("Accept", "*/*")

    current = url
    chain = []
    exchange = None
    for hop in range(max_redirects + 1):
        decision = require(guard, current, method, confirm_write=confirm_write)
        if exchange is None:
            exchange = Exchange(current, method, headers, body or b"",
                                scope_decision=decision, note=note)
            exchange.redirect_chain = chain
        parsed = urllib.parse.urlsplit(current)
        # The address is resolved and vetted once, here, and that exact address
        # is what the connection uses. This is the rebinding control.
        addresses = _vetted_addresses(guard, parsed.hostname)
        if not addresses:
            exchange.response = _error_response("no vetted address for host")
            return exchange
        address = addresses[0]
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query

        guard.wait_for_rate_limit()
        started = time.monotonic()
        resp = Response()
        resp.address = address
        conn = None
        try:
            raw, _ = _connect(parsed.scheme, parsed.hostname, port, address,
                              timeout, scope.allow_private_networks)
            if parsed.scheme == "https":
                resp.tls = TLSInfo(sock=raw)
            conn = (http.client.HTTPSConnection(parsed.hostname, port, timeout=timeout,
                                                context=ssl.create_default_context())
                    if parsed.scheme == "https"
                    else http.client.HTTPConnection(parsed.hostname, port, timeout=timeout))
            # Reuse the socket we already vetted instead of letting the
            # connection object resolve the name again.
            conn.sock = raw
            out_headers = dict(headers)
            if parsed.port not in (None, 80, 443):
                out_headers["Host"] = f"{parsed.hostname}:{parsed.port}"
            else:
                out_headers.setdefault("Host", parsed.hostname)
            # Credentials never travel to a different host than the one they
            # were given for.
            if chain and parsed.hostname != urllib.parse.urlsplit(url).hostname:
                for name in list(out_headers):
                    if name.lower() in SENSITIVE_HEADERS:
                        del out_headers[name]
            conn.request(method, target, body=body,
                         headers={k: v for k, v in out_headers.items()
                                  if k.lower() != "host"})
            guard.note_request()
            raw_resp = conn.getresponse()
            resp.status = raw_resp.status
            resp.reason = raw_resp.reason
            resp.http_version = {10: "HTTP/1.0", 11: "HTTP/1.1"}.get(
                raw_resp.version, str(raw_resp.version))
            resp.headers = {k: v for k, v in raw_resp.getheaders()}
            body_bytes = b""
            if method != "HEAD":
                # Bounded while reading: the cap applies to the socket, so an
                # oversized response cannot exhaust memory before being cut.
                try:
                    while True:
                        chunk = raw_resp.read(65536)
                        if not chunk:
                            break
                        body_bytes += chunk
                        if len(body_bytes) > max_bytes:
                            body_bytes = body_bytes[:max_bytes]
                            resp.truncated = True
                            break
                except http.client.IncompleteRead as exc:
                    # The server announced more than it sent. Keep what arrived
                    # and say so: a partial body that is reported as complete is
                    # how a truncated download becomes a corrupt artifact.
                    body_bytes += exc.partial or b""
                    resp.error = ("IncompleteRead: server closed after "
                                  f"{len(body_bytes)} bytes")
                announced = resp.content_length_header
                if (not resp.truncated and announced is not None
                        and len(body_bytes) < announced
                        and not resp.error):
                    # A server that closes early does not always make the read
                    # raise, so the length is compared explicitly. Read alone
                    # reported this response as a clean 200 with a short body,
                    # which is exactly the shape a corrupted download takes.
                    resp.error = (f"IncompleteRead: server announced {announced} "
                                  f"bytes and sent {len(body_bytes)}")
            resp.body = body_bytes
        except ScopeError:
            raise
        except Exception as exc:
            resp.error = f"{type(exc).__name__}: {exc}"[:300]
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            resp.elapsed_ms = int((time.monotonic() - started) * 1000)

        # A redirect is followed only if the next hop passes the gate again, and
        # only for the methods that are safe to repeat.
        if (follow_redirects and resp.status in (301, 302, 303, 307, 308)
                and resp.headers.get("Location") and hop < max_redirects):
            nxt = urllib.parse.urljoin(current, resp.headers["Location"])
            chain.append({"from": current, "status": resp.status,
                          "location": nxt, "bytes": len(resp.body)})
            if method in ("POST", "PUT", "PATCH", "DELETE") and resp.status == 303:
                method = "GET"                 # RFC 9110: 303 means "see other with GET"
                body = None
            next_decision = guard.check(nxt, method)
            if not next_decision:
                exchange.response = resp
                exchange.redirect_chain = chain
                guard.denials.append(dict(next_decision.as_dict(),
                                          rule="redirect_" + next_decision.rule))
                exchange.note = (note + " | redirect refused: " + next_decision.reason).strip(" |")
                return exchange
            current = nxt
            continue

        exchange.response = resp
        exchange.redirect_chain = chain
        return exchange

    return exchange


def _vetted_addresses(guard, host):
    decision = guard.check_address(host)
    if not decision:
        raise ScopeError(f"address refused for {host}: {decision.reason}")
    if _is_literal(host):
        return [host.strip("[]")]
    return guard._resolve(host)


def _is_literal(host):
    try:
        import ipaddress
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def _error_response(reason):
    resp = Response()
    resp.error = reason
    return resp


def fetch_metadata(guard, url, **kw):
    """HEAD, falling back to a ranged GET when a server rejects HEAD.

    A server that answers `405` or `501` to HEAD has not said anything about the
    resource; treating that as failure would be reporting the tool's limitation
    as a property of the target.
    """
    ex = request(guard, url, "HEAD", **kw)
    if ex.response is not None and ex.response.status in (405, 501, 400):
        ranged = dict(kw)
        ranged["headers"] = dict(kw.get("headers") or {}, Range="bytes=0-0")
        ex = request(guard, url, "GET", **ranged)
        if ex.response is not None:
            ex.note = (ex.note + " | HEAD rejected; used a one-byte range request").strip(" |")
    return ex
