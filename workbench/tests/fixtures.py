"""Deterministic local fixtures. No test in this suite touches the network.

Every byte the workbench consumes during a test run is generated here, in
process, from fixed inputs:

* a loopback HTTP server with a fixed route table, so behaviour under 401, 403,
  404, 429, redirects, truncation, oversized bodies and MIME mismatch is
  reproducible and cannot depend on a third party's uptime, rate limiting or
  willingness to be probed;
* file fixtures built by code — a real PDF with a real cross-reference table, a
  real zip, a real nested archive, a deliberately malformed archive, an archive
  whose entry name escapes its directory, and a compression bomb.

Everything is labelled. The server stamps `X-Blackheart-Fixture: true` on every
response and the file builders write a marker inside the content, so a captured
exchange or a downloaded artifact can never be mistaken for a real target's.

The loopback addresses are deliberate: they are exactly what the scope gate
refuses by default, so the tests that exercise the gate and the tests that need a
server are the same tests. Authorising 127.0.0.1 in a fixture scope is a
deliberate, explicit act — which is the behaviour the gate exists to require.
"""

from __future__ import annotations

import io
import socket
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FIXTURE_MARKER = "X-Blackheart-Fixture"
FIXTURE_NOTE = "Blackhearts test fixture — generated locally, not a real target"

# A PDF is built rather than pasted so the cross-reference offsets are correct
# and the parser is tested against a structurally valid file, not a toy.
PDF_TITLE = "BLACKHEARTS FIXTURE DOCUMENT"
PDF_AUTHOR = "Blackhearts test fixture"
PDF_TEXT_PAGE1 = "Fixture page one: allocation boundaries and the reachability rule."
PDF_TEXT_PAGE2 = "Fixture page two: extraction limits and the quarantine state."
PDF_LINK_URL = "https://fixture.invalid/blackhearts-fixture"


def _pdf_escape(text):
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(with_attachment=True, compressed=True):
    """A minimal, structurally valid PDF: 2 pages, metadata, a link, an attachment."""
    import zlib

    objects = {}

    def content_stream(text):
        raw = (f"BT /F1 12 Tf 40 700 Td ({_pdf_escape(text)}) Tj ET").encode("latin-1")
        if not compressed:
            return b"<< /Length " + str(len(raw)).encode() + b" >>\nstream\n" + raw + b"\nendstream"
        packed = zlib.compress(raw)
        return (b"<< /Length " + str(len(packed)).encode() +
                b" /Filter /FlateDecode >>\nstream\n" + packed + b"\nendstream")

    attachment = b"fixture attachment body\n" if with_attachment else None

    objects[1] = b"<< /Type /Catalog /Pages 2 0 R /Names << /EmbeddedFiles 9 0 R >> >>" \
        if with_attachment else b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[2] = b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>"
    objects[3] = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                  b"/Contents 4 0 R /Resources << /Font << /F1 7 0 R >> >> "
                  b"/Annots [8 0 R] >>")
    objects[4] = content_stream(PDF_TEXT_PAGE1)
    objects[5] = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                  b"/Contents 6 0 R /Resources << /Font << /F1 7 0 R >> >> >>")
    objects[6] = content_stream(PDF_TEXT_PAGE2)
    objects[7] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[8] = (b"<< /Type /Annot /Subtype /Link /Rect [40 690 300 710] "
                  b"/A << /Type /Action /S /URI /URI (" + PDF_LINK_URL.encode() + b") >> >>")
    if with_attachment:
        stream = attachment
        packed = zlib.compress(stream)
        objects[10] = (b"<< /Type /EmbeddedFile /Subtype /text#2Fplain /Length " +
                       str(len(packed)).encode() + b" /Filter /FlateDecode >>\nstream\n" +
                       packed + b"\nendstream")
        objects[9] = (b"<< /Names [(fixture-attachment.txt) 11 0 R] >>")
        objects[11] = (b"<< /Type /Filespec /F (fixture-attachment.txt) "
                       b"/UF (fixture-attachment.txt) /EF << /F 10 0 R >> "
                       b"/Desc (Blackhearts test fixture attachment) >>")

    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for num in sorted(objects):
        offsets[num] = len(out)
        out += f"{num} 0 obj\n".encode() + objects[num] + b"\nendobj\n"

    info_num = max(objects) + 1
    offsets[info_num] = len(out)
    out += (f"{info_num} 0 obj\n<< /Title ({_pdf_escape(PDF_TITLE)}) "
            f"/Author ({_pdf_escape(PDF_AUTHOR)}) /Producer ({_pdf_escape(FIXTURE_NOTE)}) "
            f"/CreationDate (D:20260101000000Z) >>\nendobj\n").encode()

    xref_at = len(out)
    count = info_num + 1
    out += f"xref\n0 {count}\n".encode()
    out += b"0000000000 65535 f \n"
    for num in range(1, count):
        if num in offsets:
            out += f"{offsets[num]:010d} 00000 n \n".encode()
        else:
            out += b"0000000000 65535 f \n"
    out += (f"trailer\n<< /Size {count} /Root 1 0 R /Info {info_num} 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    return bytes(out)


def build_zip(entries=None, marker=True):
    """A well-formed zip. Entries default to plain text files."""
    entries = entries or {"fixture.txt": b"Blackhearts test fixture\n"}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            if isinstance(data, str):
                data = data.encode()
            zf.writestr(name, data)
        if marker:
            zf.writestr("FIXTURE-README.txt", FIXTURE_NOTE + "\n")
    return buf.getvalue()


def build_nested_zip(depth=2):
    """An archive containing an archive, so recursion limits are exercised."""
    payload = build_zip({"leaf.txt": b"leaf of the fixture archive\n"})
    for level in range(depth):
        payload = build_zip({f"level-{level}.zip": payload})
    return payload


def build_traversal_zip():
    """A zip whose member names try to escape the extraction directory.

    Written with `../` and with an absolute path, because both have to be
    refused and neither can be caught by normalising only one of them.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../escaped-relative.txt", "should never be written")
        # The path is the fixture: an archive entry that claims to be absolute
        # must be refused by the extractor. Nothing is written to /tmp here.
        zf.writestr("/tmp/escaped-absolute.txt", "should never be written")  # nosec B108
        zf.writestr("nested/../../escaped-two-levels.txt", "should never be written")
        zf.writestr("safe/inside.txt", "this one is fine")
    return buf.getvalue()


def build_bomb_zip(megabytes=8):
    """A compression bomb: a small archive that expands to a lot of bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("bomb.bin", b"\0" * (megabytes * 1024 * 1024))
    return buf.getvalue()


def build_many_entries_zip(count=500):
    return build_zip({f"entry-{i:04d}.txt": b"x" for i in range(count)}, marker=False)


def build_malformed_zip():
    """A header that claims to be a zip and is not."""
    good = bytearray(build_zip())
    # Corrupt the local file header of the first entry, keeping the signature so
    # the file is still detected as an archive by magic bytes.
    good[30:34] = b"\xff\xff\xff\xff"
    return bytes(good[:200])


def build_tar_gz():
    import gzip
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo("fixture.txt")
        payload = b"Blackhearts test fixture\n"
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "BlackheartsFixture/1.0"

    def log_message(self, *args):        # silence the default stderr chatter
        pass

    # -- helpers --------------------------------------------------------
    def _record(self):
        self.server.hits.append({
            "method": self.command,
            "path": self.path,
            "headers": {k: v for k, v in self.headers.items()},
        })

    def _send(self, status, body=b"", content_type="text/plain; charset=utf-8",
              headers=None, content_length=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header(FIXTURE_MARKER, "true")
        announced = content_length if content_length is not None else len(body)
        self.send_header("Content-Length", str(announced))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _fixture_host(self):
        return f"127.0.0.1:{self.server.server_address[1]}"

    # -- routes ---------------------------------------------------------
    def do_GET(self):                    # noqa: N802 - required by BaseHTTPRequestHandler
        path = self.path.split("?")[0]
        query = self.path.split("?", 1)[1] if "?" in self.path else ""
        self._record()

        if path == "/":
            self._send(200, _index_html(self._fixture_host()), "text/html; charset=utf-8")
        elif path == "/robots.txt":
            self._send(200, "User-agent: *\nDisallow: /private\nSitemap: http://%s/sitemap.xml\n"
                            % self._fixture_host())
        elif path == "/sitemap.xml":
            self._send(200, _sitemap(self._fixture_host()), "application/xml")
        elif path == "/openapi.json":
            self._send(200, _openapi(), "application/json")
        elif path == "/text":
            payload = b"fixture text body\n"
            rng = self.headers.get("Range")
            if rng and rng.startswith("bytes="):
                spec = rng.split("=", 1)[1].split("-")
                start = int(spec[0] or 0)
                end = int(spec[1]) if len(spec) > 1 and spec[1] else len(payload) - 1
                end = min(end, len(payload) - 1)
                partial = payload[start:end + 1]
                self.send_response(206)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Range", f"bytes {start}-{end}/{len(payload)}")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header(FIXTURE_MARKER, "true")
                self.send_header("Content-Length", str(len(partial)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(partial)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header(FIXTURE_MARKER, "true")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)
        elif path == "/json":
            self._send(200, '{"items":[{"id":1,"name":"alpha"},{"id":2,"name":"beta"}],'
                            '"total":2,"page":1}', "application/json")
        elif path == "/json-alt":
            self._send(200, '{"items":[{"id":1,"name":"alpha"},{"id":2,"name":"gamma"}],'
                            '"total":3,"page":1,"extra":true}', "application/json")
        elif path == "/echo":
            import json as _json
            body = _json.dumps({
                "method": self.command, "path": self.path,
                "headers": {k: v for k, v in self.headers.items()},
                "fixture": True,
            }, indent=2)
            self._send(200, body, "application/json")
        elif path == "/file.pdf":
            self._send(200, build_pdf(), "application/pdf")
        elif path == "/data.zip":
            self._send(200, build_zip(), "application/zip")
        elif path == "/nested.zip":
            self._send(200, build_nested_zip(), "application/zip")
        elif path == "/malformed.zip":
            self._send(200, build_malformed_zip(), "application/zip")
        elif path == "/bomb.zip":
            self._send(200, build_bomb_zip(), "application/zip")
        elif path == "/archive.tar.gz":
            self._send(200, build_tar_gz(), "application/gzip")
        elif path == "/redirect":
            self._send(302, "", headers={"Location": "/text"})
        elif path == "/redirect-chain":
            self._send(301, "", headers={"Location": "/redirect"})
        elif path == "/redirect-offhost":
            # TEST-NET-2 (RFC 5737): reserved for documentation, never routed.
            self._send(302, "", headers={"Location": "http://198.51.100.7/landing"})
        elif path == "/redirect-loop":
            self._send(302, "", headers={"Location": "/redirect-loop"})
        elif path == "/needs-auth":
            self._send(401, "authentication required",
                       headers={"WWW-Authenticate": 'Basic realm="fixture"'})
        elif path == "/forbidden":
            self._send(403, "forbidden")
        elif path == "/unavailable-legal":
            self._send(451, "unavailable for legal reasons")
        elif path == "/proxy-auth":
            self._send(407, "proxy authentication required",
                       headers={"Proxy-Authenticate": 'Basic realm="fixture"'})
        elif path == "/rate-limited":
            self._send(429, "too many requests", headers={"Retry-After": "30"})
        elif path == "/missing":
            self._send(404, "not found")
        elif path == "/big":
            size = int(dict(p.split("=", 1) for p in query.split("&") if "=" in p)
                       .get("size", "2000000")) if query else 2000000
            size = max(1, min(size, 40_000_000))
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(size))
            self.send_header(FIXTURE_MARKER, "true")
            self.end_headers()
            chunk = b"A" * 65536
            sent = 0
            try:
                while sent < size:
                    self.wfile.write(chunk[:min(65536, size - sent)])
                    sent += min(65536, size - sent)
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif path == "/truncated":
            body = b"B" * 1000
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", "5000")   # more than is sent
            self.send_header(FIXTURE_MARKER, "true")
            self.end_headers()
            try:
                self.wfile.write(body)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True
        elif path == "/slow":
            time.sleep(2.0)
            self._send(200, "slow fixture response\n")
        elif path == "/bad-type":
            self._send(200, "<html><body>fixture html served as octet-stream</body></html>",
                       "application/octet-stream")
        elif path == "/no-type":
            self.send_response(200)
            self.send_header("Content-Length", "23")
            self.send_header(FIXTURE_MARKER, "true")
            self.end_headers()
            self.wfile.write(b"fixture with no type\n")
        elif path == "/hardened":
            self._send(200, "hardened fixture\n", headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'none'",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
            })
        elif path == "/soft":
            self._send(200, "soft fixture\n", headers={"Server": "BlackheartsFixture/1.0"})
        elif path == "/setcookie-hardened":
            self._send(200, "cookies set",
                       headers={"Set-Cookie": "sid=fixture-not-a-real-value; Path=/; "
                                              "HttpOnly; Secure; SameSite=Strict"})
        elif path == "/setcookie-soft":
            self._send(200, "cookies set",
                       headers={"Set-Cookie": "sid=fixture-not-a-real-value; Path=/"})
        elif path == "/cors-wildcard":
            self._send(200, "cors", headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            })
        elif path == "/cors-reflected":
            origin = self.headers.get("Origin", "https://fixture.invalid")
            self._send(200, "cors", headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            })
        elif path == "/cacheable":
            self._send(200, "cacheable", headers={"Cache-Control": "public, max-age=3600"})
        elif path == "/reflect":
            value = query.split("=", 1)[1] if "=" in query else ""
            self._send(200, f"<html><body><p>You searched for: {value}</p></body></html>",
                       "text/html; charset=utf-8")
        elif path == "/encoded":
            value = query.split("=", 1)[1] if "=" in query else ""
            self._send(200, f"<html><body><p>You searched for: {value}</p></body></html>",
                       "text/html; charset=utf-8")
        elif path == "/open-redirect":
            target = query.split("=", 1)[1] if "=" in query else "/text"
            self._send(302, "", headers={"Location": target})
        elif path.startswith("/api/items/"):
            item_id = path.rsplit("/", 1)[-1]
            self._send(200, f'{{"id":"{item_id}","owner":"fixture-owner","data":"fixture"}}',
                       "application/json")
        elif path == "/counts":
            import json as _json
            self._send(200, _json.dumps({"requests": len(self.server.hits)}), "application/json")
        elif path == "/hits":
            import json as _json
            self._send(200, _json.dumps({"hits": self.server.hits[:50]}), "application/json")
        else:
            self._send(404, "not found")

    def do_HEAD(self):                   # noqa: N802
        self.do_GET()

    def do_POST(self):                   # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self._record()
        import json as _json
        self._send(200, _json.dumps({
            "method": "POST", "path": self.path, "bytes": len(body),
            "content_type": self.headers.get("Content-Type", ""),
            "fixture": True,
        }), "application/json")

    def do_PUT(self):                    # noqa: N802
        self.do_POST()

    def do_DELETE(self):                 # noqa: N802
        self._record()
        self._send(200, '{"deleted":true,"fixture":true}', "application/json")

    def do_OPTIONS(self):                # noqa: N802
        self._send(204, "", headers={"Allow": "GET, HEAD, POST, OPTIONS"})


def _index_html(host):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Blackhearts fixture page</title></head>
<body>
<h1>Fixture page</h1>
<p>Generated locally for the workbench test suite. Not a real target.</p>
<ul>
  <li><a href="/text">plain text</a></li>
  <li><a href="/file.pdf">fixture document</a></li>
  <li><a href="/data.zip">fixture archive</a></li>
  <li><a href="https://fixture.invalid/external">an external link that must not be crawled</a></li>
</ul>
<form action="/echo" method="post">
  <input type="text" name="username" value="">
  <input type="password" name="password" value="">
  <input type="hidden" name="csrf_token" value="fixture-not-a-real-token">
  <select name="role"><option>viewer</option><option>editor</option></select>
  <textarea name="notes"></textarea>
  <input type="file" name="attachment">
  <button type="submit">Send</button>
</form>
<script src="/fixture.js"></script>
</body></html>
"""


def _sitemap(host):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://{host}/</loc></url>
  <url><loc>http://{host}/text</loc></url>
  <url><loc>http://{host}/file.pdf</loc></url>
</urlset>
"""


def _openapi():
    return """{
  "openapi": "3.0.0",
  "info": {"title": "Blackhearts fixture API", "version": "1.0.0"},
  "paths": {
    "/api/items/{id}": {
      "get": {"parameters": [{"name": "id", "in": "path", "required": true}]},
      "delete": {"parameters": [{"name": "id", "in": "path", "required": true}]}
    },
    "/echo": {"post": {"summary": "echo a body"}}
  }
}"""


class FixtureServer:
    """A loopback server bound to an ephemeral port. Use as a context manager."""

    def __init__(self):
        self._server = None
        self._thread = None

    def __enter__(self):
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.daemon_threads = True
        self._server.hits = []
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self.stop()
        return False

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    @property
    def port(self):
        return self._server.server_address[1]

    @property
    def base(self):
        return f"http://127.0.0.1:{self.port}"

    def url(self, path):
        return f"{self.base}{path}"

    @property
    def hits(self):
        return list(self._server.hits)

    def reset_hits(self):
        self._server.hits = []


def scope_data(base_url=None, methods=("GET", "HEAD", "OPTIONS"), **overrides):
    """A scope object authorising a fixture server, for tests only.

    `allow_private_networks` is set because the fixtures are on loopback — the
    one situation where that flag is legitimate, and the tests that prove the
    flag is *required* use a scope without it.
    """
    data = {
        "targets": [base_url or "http://127.0.0.1"],
        "allowed_hosts": ["127.0.0.1", "localhost"],
        "allowed_paths": [],
        "excluded_hosts": [],
        "excluded_paths": ["/private", "/admin"],
        "allowed_methods": list(methods),
        "max_requests": 200,
        "max_concurrency": 4,
        "max_response_bytes": 1_000_000,
        "max_redirects": 5,
        "timeout_s": 5.0,
        "min_interval_s": 0.0,
        "authorized_until": None,
        "allow_private_networks": True,
        "notes": "Test fixture scope. Loopback only.",
    }
    data.update(overrides)
    return data


def write_scope(tmpdir, **overrides):
    """Write a fixture scope to disk and return its path."""
    import json
    import os

    path = os.path.join(tmpdir, "scope.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(scope_data(**overrides), fh, indent=2)
    return path


def guess_free_port():
    """A port that is free right now, for tests that need a closed one."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


__all__ = [
    "FIXTURE_MARKER", "FIXTURE_NOTE", "FixtureServer", "scope_data",
    "write_scope", "build_pdf", "build_zip", "build_nested_zip",
    "build_traversal_zip", "build_bomb_zip", "build_many_entries_zip",
    "build_malformed_zip", "build_tar_gz", "guess_free_port",
    "PDF_TITLE", "PDF_AUTHOR", "PDF_TEXT_PAGE1", "PDF_TEXT_PAGE2", "PDF_LINK_URL",
]
