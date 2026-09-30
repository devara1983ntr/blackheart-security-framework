"""Acquisition with provenance, and the manifest that records it.

The rule this module exists to keep
-----------------------------------
A file is written to disk under one condition only: the target served it, in
full, to a request that the scope gate allowed, and the bytes on disk hash to the
bytes that were received. Everything else is recorded as a failure, a block or a
skip — with the HTTP evidence that says why — and no file is written.

Why that matters more than it sounds
------------------------------------
"Downloaded 42 files" is a claim. Each of those files is either something the
target served or something the tool produced, and a reader of the report has no
way to tell which unless the manifest says so. So the manifest records, per
acquisition: the URL asked for, the URL that finally answered, the status, the
declared content type, the size, the SHA-256 of the file on disk, the redirect
chain, the licence note, the authorization scope, the sniffed file type, whether
the extension matches the content, and the extraction status.

What it will not do
-------------------
* A 401, 402, 403, 407 or 451 is a stop, not an obstacle. The path ends there.
* A subscription wall, a signed URL that has expired, a DRM-protected payload or
  an interstitial challenge is not something to get past. It is recorded as
  blocked, with the evidence, and the entry names the authorised route instead:
  the publisher's own interface, an institutional login, a purchase, a library
  request, or the open-access copy the publisher or author published themselves.
* No mirror hunting, no cache scraping, no credential guessing, no "try until
  something works". There is no code path here that retries with a different
  identity, because there is no second identity to try.
* A truncated body is a failure. The bytes that arrived are not written as the
  artifact, because a partial PDF presented as a downloaded PDF is how a report
  ends up quoting a document nobody can open.

`sniff_type` lives here rather than in `extract.py` because the manifest's file
type is written at acquisition time, before anything is parsed.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse

from . import evidence as ev
from . import http_client as hc

STATUSES = ("success", "failed", "blocked", "skipped")

# Statuses where the target is telling us the answer is no. Each is terminal for
# that path: the entry records what was asked, what came back, and nothing here
# attempts the request again in another shape.
BLOCKING_STATUSES = {
    401: "authentication required",
    402: "payment required",
    403: "access forbidden",
    407: "proxy authentication required",
    451: "unavailable for legal reasons",
}

# Bodies that mean an intermediary is standing between the client and the
# document. When one of these arrives in place of the requested content type, the
# bytes are not the document and are not written as if they were.
CHALLENGE_MARKERS = (
    "captcha",
    "are you a human",
    "cf-chl-",
    "just a moment",
    "checking your browser",
    "enable javascript and cookies to continue",
    "attention required! | cloudflare",
    "pardon our interruption",
    "verify you are a human",
    "access to this page has been denied",
    "turnstile",
)

# Magic prefixes used for the type check. Small on purpose: this is not a MIME
# library, it is the check that an artifact served as a PDF is not an HTML login
# page.
MAGIC = (
    (b"%PDF-", "pdf"),
    (b"PK\x03\x04", "zip"),
    (b"PK\x05\x06", "zip"),
    (b"\x1f\x8b", "gzip"),
    (b"ustar", "tar"),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "ole"),
    (b"{\\rtf", "rtf"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"RIFF", "riff"),
    (b"\x7fELF", "elf"),
    (b"MZ", "pe"),
)

TEXT_TYPES = ("text/", "application/json", "application/xml", "application/javascript")

# Types a document download is expected to be. Used only to decide whether an
# HTML body is the document or a page standing in front of it.
DOCUMENT_TYPES = ("application/pdf", "application/zip", "application/gzip",
                  "application/x-tar", "application/octet-stream", "text/csv",
                  "application/vnd.openxmlformats-officedocument",
                  "application/msword", "application/epub+zip")

EXTENSION_TYPES = {
    ".pdf": "pdf", ".zip": "zip", ".gz": "gzip", ".tgz": "gzip", ".tar": "tar",
    ".json": "json", ".xml": "xml", ".csv": "csv", ".txt": "text", ".md": "text",
    ".html": "html", ".htm": "html", ".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg",
    ".gif": "gif", ".svg": "svg", ".doc": "ole", ".docx": "zip", ".xlsx": "zip",
    ".pptx": "zip", ".rtf": "rtf", ".epub": "zip",
}

UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


class FetchError(Exception):
    """Raised when an acquisition cannot be attempted as asked."""


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sniff_type(data, content_type="", url=""):
    """A short name for what the bytes are, from their prefix.

    Returns `(file_type, confident)`. `confident` is False when the answer came
    from the declared type or the URL rather than from the bytes, which is the
    case for text formats that have no magic number.
    """
    prefix = bytes(data or b"")[:64]
    for magic, name in MAGIC:
        if prefix.startswith(magic):
            return name, True
    declared = (content_type or "").split(";")[0].strip().lower()
    if declared.startswith("text/html") or b"<html" in prefix[:512].lower():
        return "html", declared.startswith("text/html")
    if declared in ("application/json",) or prefix[:1] in (b"{", b"["):
        return "json", declared == "application/json"
    if declared.startswith("text/"):
        return "text", False
    path = urllib.parse.urlsplit(url or "").path.lower()
    for extension, name in EXTENSION_TYPES.items():
        if path.endswith(extension):
            return name, False
    return "unknown", False


def extension_matches_content(filename, file_type):
    """Whether the file name's extension describes the sniffed type it holds."""
    extension = os.path.splitext(filename or "")[1].lower()
    expected = EXTENSION_TYPES.get(extension)
    if expected is None or file_type in ("unknown", None):
        return None
    return expected == file_type


DOCUMENT_EXTENSIONS = (".pdf", ".zip", ".gz", ".tgz", ".tar", ".doc", ".docx",
                       ".xlsx", ".pptx", ".epub", ".rtf", ".csv")


def expects_a_document(url, expect=None):
    """Whether this acquisition was meant to return a file rather than a page.

    `expect="document"` says so explicitly, which is what the command surface
    passes. Without it the URL's extension is the only evidence available, and a
    URL that ends in nothing at all cannot be judged — the limit is real, and the
    manifest records the content type so a reader can see what came back.
    """
    if expect == "document":
        return True
    if expect == "page":
        return False
    path = urllib.parse.urlsplit(url or "").path.lower()
    return any(path.endswith(extension) for extension in DOCUMENT_EXTENSIONS)


def looks_like_a_challenge(body_text, content_type, requested_type=""):
    """Whether a response is an interstitial rather than the document.

    Only consulted for responses that were expected to carry a document and
    arrived as HTML, so a page that merely mentions the word "captcha" is not
    mistaken for one when it was the page that was asked for.
    """
    if "html" not in (content_type or "").lower():
        return ""
    lowered = (body_text or "")[:20000].lower()
    for marker in CHALLENGE_MARKERS:
        if marker in lowered:
            return marker
    return ""


def safe_filename(url, content_type="", prefix=""):
    """A filename for a downloaded artifact, derived from the URL's last segment.

    The name is sanitised rather than trusted: a `Content-Disposition` header or
    a path segment is attacker-influenced input, and a download directory that
    can be escaped by a filename is a write-anywhere primitive.
    """
    path = urllib.parse.urlsplit(url or "").path
    name = os.path.basename(path) or ""
    name = urllib.parse.unquote(name)
    name = name.replace("\\", "_").replace("/", "_")
    name = UNSAFE_FILENAME.sub("_", name).strip("._")
    if not name:
        name = "download"
    if len(name) > 120:
        stem, extension = os.path.splitext(name)
        name = stem[:100] + extension[:19]
    if "." not in name:
        extension = {"application/pdf": ".pdf", "application/json": ".json",
                     "text/html": ".html", "text/plain": ".txt",
                     "application/zip": ".zip"}.get((content_type or "").split(";")[0].strip())
        if extension:
            name += extension
    return f"{prefix}{name}"


def _inside(directory, filename):
    """Guard against a filename that resolves outside the destination."""
    target = os.path.realpath(os.path.join(directory, filename))
    root = os.path.realpath(directory)
    return target == root or target.startswith(root + os.sep)


def authorized_paths(url, status=None, reason=""):
    """The legitimate ways to get something the target would not serve.

    Written as text a person can act on, and deliberately not as anything the
    tool can execute: the answer to "I am not allowed to read this" is to ask
    the person who can grant permission, not to find another route.
    """
    parsed = urllib.parse.urlsplit(url or "")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    paths = []
    if status in (401, 407) or "authentication" in reason:
        paths.append({
            "route": "the site's own login",
            "detail": ("Authenticate with your own credentials through the target's "
                       "own login, then re-run with an authorised session supplied "
                       "through the mechanism the engagement documents."),
        })
    if status in (402, 451) or "payment" in reason or "legal" in reason:
        paths.append({
            "route": "the publisher's own access route",
            "detail": ("Purchase, subscribe, or ask your institution's library. If the "
                       "item is behind a paywall, the publisher or the author may have "
                       "published an open-access copy — look for it at the publisher's "
                       "own page for the item rather than at a third-party mirror."),
        })
    if status == 403:
        paths.append({
            "route": "ask the asset owner",
            "detail": ("The request was refused. Ask the owner whether the resource is "
                       "meant to be reachable, and whether your identity or network "
                       "is expected to reach it. Do not retry with altered headers."),
        })
    paths.append({
        "route": "documented public metadata",
        "detail": ("The item's public metadata (title, author, identifier, licence) is "
                   "usually readable without the item itself. Record that, and record "
                   "the official page for it as the citation."),
    })
    paths.append({
        "route": "stop",
        "detail": ("This tool stops here. It does not use mirrors, caches, proxies, "
                   "altered identities or expired links to obtain a copy."),
    })
    return {"official_url": origin, "requested_url": url, "routes": paths}


class Acquisition:
    """One attempt to obtain one resource, and everything known about it."""

    def __init__(self, entry_id, source_url, scope, *, license_note="", note=""):
        self.id = entry_id
        self.source_url = source_url
        self.scope = scope or {}
        self.license_note = license_note
        self.note = note
        self.status = "skipped"
        self.final_url = source_url
        self.http_status = None
        self.content_type = None
        self.bytes = 0
        self.sha256 = None
        self.timestamp = now()
        self.redirect_chain = []
        self.file = None
        self.file_type = None
        self.confident_type = False
        self.extension_matches_content = None
        self.extraction_status = "not_started"
        self.blocked_reason = None
        self.access = None
        self.public_metadata = {}
        self.error = None
        self.warnings = []

    @property
    def downloaded(self):
        """Whether a file was written. True only for a completed acquisition."""
        return self.status == "success" and bool(self.file)

    def as_dict(self):
        return {
            "id": self.id,
            "source_url": self.source_url,
            "final_url": self.final_url,
            "status": self.status,
            "http_status": self.http_status,
            "content_type": self.content_type,
            "bytes": self.bytes,
            "sha256": self.sha256,
            "timestamp": self.timestamp,
            "redirect_chain": self.redirect_chain,
            "file": self.file,
            "file_type": self.file_type,
            "type_confident": self.confident_type,
            "extension_matches_content": self.extension_matches_content,
            "extraction_status": self.extraction_status,
            "license_note": self.license_note,
            "authorization_scope": self.scope,
            "blocked_reason": self.blocked_reason,
            "access": self.access,
            "public_metadata": self.public_metadata,
            "error": self.error,
            "warnings": list(self.warnings),
            "note": self.note,
            "downloaded": self.downloaded,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild an entry from a written manifest.

        Two invocations of the same command over the same directory must not
        produce a manifest that forgets the first one, so the CLI reads the file
        back with this. Every field is copied explicitly rather than with
        `update`, so a manifest written by a different version cannot smuggle an
        attribute in and have it silently ignored on the next write.
        """
        acquisition = cls(data.get("id", ""), data.get("source_url", ""),
                          data.get("authorization_scope") or {},
                          license_note=data.get("license_note") or "",
                          note=data.get("note") or "")
        acquisition.final_url = data.get("final_url", acquisition.source_url)
        acquisition.status = data.get("status", "skipped")
        acquisition.http_status = data.get("http_status")
        acquisition.content_type = data.get("content_type")
        acquisition.bytes = data.get("bytes", 0)
        acquisition.sha256 = data.get("sha256")
        acquisition.timestamp = data.get("timestamp", acquisition.timestamp)
        acquisition.redirect_chain = list(data.get("redirect_chain") or [])
        acquisition.file = data.get("file")
        acquisition.file_type = data.get("file_type")
        acquisition.confident_type = bool(data.get("type_confident"))
        acquisition.extension_matches_content = data.get("extension_matches_content")
        acquisition.extraction_status = data.get("extraction_status", "not_started")
        acquisition.blocked_reason = data.get("blocked_reason")
        acquisition.access = data.get("access")
        acquisition.public_metadata = dict(data.get("public_metadata") or {})
        acquisition.error = data.get("error")
        acquisition.warnings = list(data.get("warnings") or [])
        return acquisition

    def summary_line(self):
        detail = self.final_url if self.final_url == self.source_url else \
            f"{self.source_url} -> {self.final_url}"
        parts = [f"[{self.id}] {self.status:7} {self.http_status} {detail}"]
        if self.file:
            parts.append(f"{self.bytes} bytes -> {self.file} ({self.file_type})")
        if self.blocked_reason:
            parts.append(self.blocked_reason)
        if self.error:
            parts.append(self.error)
        return " | ".join(str(p) for p in parts)


class Manifest:
    """`downloads/manifest.json`: every acquisition, in order, with hashes."""

    VERSION = 1

    def __init__(self, directory, scope_file=None, scope=None, name="downloads"):
        self.directory = directory
        self.scope_file = scope_file
        self.scope = scope or {}
        self.name = name
        self.entries = []
        self.started_at = now()
        self.next_number = 1

    def add(self, acquisition):
        if acquisition.status not in STATUSES:
            raise FetchError(f"unknown acquisition status {acquisition.status!r}")
        self.entries.append(acquisition)
        return acquisition

    @classmethod
    def load(cls, path, *, directory=None, scope_file=None, scope=None):
        """Read a written manifest so a later run appends to it.

        The entries are reconstructed rather than kept as dictionaries: the
        manifest is the record of what was obtained, and a run that starts by
        forgetting the previous run's entries would rewrite that record with a
        shorter one. Numbering continues from the highest `Dnnnn` present, so ids
        stay unique even if an entry was removed by hand.
        """
        if not os.path.isfile(path):
            return cls(directory or os.path.dirname(os.path.abspath(path)),
                       scope_file=scope_file, scope=scope)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        manifest = cls(directory or os.path.dirname(os.path.abspath(path)),
                       scope_file=scope_file if scope_file is not None
                       else data.get("scope_file"),
                       scope=scope if scope is not None
                       else (data.get("authorization_scope") or {}),
                       name=data.get("name", "downloads"))
        manifest.started_at = data.get("started_at", manifest.started_at)
        for entry in data.get("entries") or []:
            manifest.entries.append(Acquisition.from_dict(entry))
        highest = 0
        for entry in manifest.entries:
            entry_id = entry.id or ""
            if entry_id.startswith("D") and entry_id[1:].isdigit():
                highest = max(highest, int(entry_id[1:]))
        manifest.next_number = highest + 1
        return manifest

    def next_id(self):
        number = getattr(self, "next_number", len(self.entries) + 1)
        self.next_number = number + 1
        return f"D{number:04d}"

    def counts(self):
        counts = {status: 0 for status in STATUSES}
        for entry in self.entries:
            counts[entry.status] += 1
        return counts

    def as_dict(self):
        return {
            "manifest_version": self.VERSION,
            "name": self.name,
            "generated_at": now(),
            "started_at": self.started_at,
            "tool": "blackheart-workbench",
            "tool_version": ev.provenance_for({})["tool_version"],
            "scope_file": self.scope_file,
            "authorization_scope": self.scope,
            "directory": os.path.basename(os.path.normpath(self.directory)),
            "counts": self.counts(),
            "total": len(self.entries),
            "entries": [entry.as_dict() for entry in self.entries],
            "note": ("`success` means the target served the bytes and the SHA-256 in "
                     "this file is of the bytes on disk. `blocked` and `failed` entries "
                     "have no file. No entry is ever recorded as downloaded on the "
                     "strength of a redirect, a challenge page or a partial body."),
        }

    def write(self, path=None):
        directory = os.path.dirname(path) if path else self.directory
        os.makedirs(directory, exist_ok=True)
        path = path or os.path.join(self.directory, "manifest.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.as_dict(), fh, indent=2, sort_keys=True)
        return path

    @staticmethod
    def verify(path):
        """Re-hash every file the manifest claims, and report what disagrees.

        A manifest that lists a file which is not there, or whose hash no longer
        matches, is the difference between a record of what was obtained and a
        list of what somebody hoped was obtained.
        """
        problems = []
        if not os.path.isfile(path):
            return [f"{path} not found"]
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        directory = os.path.dirname(os.path.abspath(path))
        for entry in manifest.get("entries", []):
            if entry.get("status") == "success":
                if not entry.get("file"):
                    problems.append(f"{entry.get('id')}: success without a file name")
                    continue
                target = os.path.join(directory, entry["file"])
                if not os.path.isfile(target):
                    problems.append(f"{entry.get('id')}: file missing: {entry['file']}")
                    continue
                digest = ev.file_sha256(target)
                if digest != entry.get("sha256"):
                    problems.append(f"{entry.get('id')}: hash mismatch for {entry['file']} "
                                    f"({digest[:12]} != {str(entry.get('sha256'))[:12]})")
            elif entry.get("file"):
                problems.append(f"{entry.get('id')}: status {entry.get('status')} names a file")
            if entry.get("status") not in STATUSES:
                problems.append(f"{entry.get('id')}: unknown status {entry.get('status')!r}")
        return problems


def _block(acquisition, record, status, reason):
    """Record a refused path: what came back, and where the legitimate route is."""
    response = record.get("response") or {}
    acquisition.status = "blocked"
    acquisition.blocked_reason = reason
    acquisition.final_url = record.get("final_url") or record.get("url") or acquisition.source_url
    acquisition.http_status = response.get("status")
    acquisition.content_type = response.get("content_type")
    acquisition.redirect_chain = record.get("redirect_chain") or []
    acquisition.access = authorized_paths(acquisition.final_url, status, reason)
    acquisition.access["http_evidence"] = {
        "status": response.get("status"),
        "reason": response.get("reason"),
        "content_type": response.get("content_type"),
        "headers": hc.redact_headers(response.get("headers") or {}),
        "bytes_received": response.get("bytes"),
    }
    return acquisition


def acquire(guard, url, manifest, *, history=None, filename=None, max_bytes=None,
            expected_sha256=None, license_note="", note="", allow_partial=False,
            expect=None):
    """Ask for one resource and record the outcome, whatever the outcome is.

    Returns the `Acquisition`, which is also added to the manifest. Nothing is
    raised for an HTTP status: a refusal is a result, and one that the report
    needs. `ScopeError` is likewise recorded rather than raised, so a run over a
    list of URLs finishes and says which URLs it was not allowed to ask for.
    """
    acquisition = Acquisition(manifest.next_id(), url, manifest.scope,
                              license_note=license_note, note=note)
    os.makedirs(manifest.directory, exist_ok=True)
    try:
        exchange = hc.request(guard, url, "GET", max_bytes=max_bytes,
                              note=f"acquire:{note or 'download'}")
    except Exception as exc:                                  # ScopeError included
        acquisition.status = "blocked"
        acquisition.blocked_reason = f"not permitted by the scope file: {exc}"
        acquisition.error = f"{type(exc).__name__}: {exc}"
        acquisition.access = authorized_paths(url, None, "scope")
        return manifest.add(acquisition)

    record = exchange.record()
    if history is not None:
        history.add(exchange, tag="acquire")
    response = record.get("response") or {}
    status = response.get("status")
    acquisition.http_status = status
    acquisition.content_type = response.get("content_type")
    acquisition.final_url = record.get("final_url") or record.get("url") or url
    acquisition.redirect_chain = record.get("redirect_chain") or []
    acquisition.bytes = response.get("bytes") or 0

    # -- refusals, in the order that decides the outcome
    if status in BLOCKING_STATUSES:
        return manifest.add(_block(acquisition, record, status,
                                   BLOCKING_STATUSES[status]))
    if response.get("error"):
        acquisition.status = "failed"
        acquisition.error = response["error"]
        return manifest.add(acquisition)
    if status is None:
        acquisition.status = "failed"
        acquisition.error = "no response: the request did not complete"
        return manifest.add(acquisition)
    if status >= 400:
        acquisition.status = "failed"
        acquisition.error = f"HTTP {status} {response.get('reason') or ''}".strip()
        return manifest.add(acquisition)

    body = (response.get("body_text") or "").encode("utf-8", errors="replace")
    # Whether this was meant to be a document is a property of the request, not
    # of the response. Reading it off the response content type meant an
    # interstitial served as text/html was never recognised as an interstitial:
    # the check asked "is this HTML?" of a page that had already told us it was.
    requested_document = expects_a_document(acquisition.final_url, expect)
    challenge = looks_like_a_challenge(response.get("body_text"),
                                       acquisition.content_type)
    # A challenge blocks a document outright, and is *recorded* on a page. The
    # asymmetry is deliberate — a page about captchas is a legitimate page, and
    # blocking every HTML response that contains the word would be a false
    # positive on the framework's own documentation — but silence was not: a page
    # carrying a challenge marker used to be written as a plain success, with
    # nothing in the entry to say the marker had been seen. It is now recorded in
    # both cases, so a reader of the manifest can see it either way.
    if challenge and requested_document:
        return manifest.add(_block(
            acquisition, record, status,
            f"an interstitial challenge stood in place of the document ({challenge!r})"))
    if response.get("truncated") and not allow_partial:
        acquisition.status = "failed"
        acquisition.error = ("the body was cut at the size limit; the artifact is not "
                            "complete and was not written")
        return manifest.add(acquisition)

    data = body
    digest = ev.sha256_bytes(data)
    if expected_sha256 and digest.lower() != expected_sha256.lower():
        acquisition.status = "failed"
        acquisition.sha256 = digest
        acquisition.error = (f"integrity check failed: expected {expected_sha256[:16]}..., "
                             f"the target served {digest[:16]}...")
        return manifest.add(acquisition)

    name = filename or safe_filename(acquisition.final_url, acquisition.content_type)
    if not _inside(manifest.directory, name):
        acquisition.status = "failed"
        acquisition.error = f"refused a filename that escapes the download directory: {name!r}"
        return manifest.add(acquisition)
    target = os.path.join(manifest.directory, name)
    stem, extension = os.path.splitext(name)
    counter = 2
    while os.path.exists(target):
        target = os.path.join(manifest.directory, f"{stem}-{counter}{extension}")
        counter += 1
    with open(target, "wb") as fh:
        fh.write(data)

    # The hash is taken from the file on disk, which is what a reader of the
    # manifest will verify against.
    acquisition.file = os.path.basename(target)
    acquisition.sha256 = ev.file_sha256(target)
    acquisition.bytes = os.path.getsize(target)
    acquisition.file_type, acquisition.confident_type = sniff_type(
        data, acquisition.content_type, acquisition.final_url)
    acquisition.extension_matches_content = extension_matches_content(
        acquisition.file, acquisition.file_type)
    if acquisition.extension_matches_content is False:
        acquisition.warnings.append(
            f"the file name says {os.path.splitext(acquisition.file)[1]} but the bytes "
            f"are {acquisition.file_type}")
    if requested_document and acquisition.file_type == "html":
        acquisition.warnings.append(
            "an HTML document was served where a file was expected: it may be a landing "
            "page, a login page or an error page rather than the resource")
    if challenge:
        # Recorded whether it blocked or not, so a page saved with a challenge
        # marker in it says so in the manifest instead of reading as a clean page.
        acquisition.warnings.append(
            f"this response carries an interstitial challenge marker ({challenge!r}); it "
            f"was written because a page was asked for, and it is the marker's presence "
            f"that makes it untrustworthy as page content")
    if not acquisition.confident_type:
        acquisition.warnings.append(
            "the file type was inferred from the declared type or the URL, not from a "
            "magic number in the bytes")
    if acquisition.redirect_chain:
        hosts = {hop.get("location", "") for hop in acquisition.redirect_chain}
        sources = {urllib.parse.urlsplit(acquisition.final_url).hostname,
                   urllib.parse.urlsplit(acquisition.source_url).hostname}
        if any(urllib.parse.urlsplit(h).hostname not in sources for h in hosts):
            acquisition.warnings.append(
                "the request was redirected off the original host; the chain is recorded")
    acquisition.status = "success"
    acquisition.timestamp = now()
    return manifest.add(acquisition)


def skip(manifest, url, reason, *, license_note=""):
    """Record a URL that was deliberately not requested, and why."""
    acquisition = Acquisition(manifest.next_id(), url, manifest.scope,
                              license_note=license_note)
    acquisition.status = "skipped"
    acquisition.blocked_reason = reason
    return manifest.add(acquisition)


def verify_manifest(path):
    """Re-check a written manifest. Returns the list of problems, empty if clean."""
    return Manifest.verify(path)


def manifest_lines(manifest, limit=40):
    """A readable summary of an acquisition run."""
    counts = manifest.counts()
    lines = [
        f"Acquisition: {counts['success']} obtained, {counts['blocked']} blocked, "
        f"{counts['failed']} failed, {counts['skipped']} skipped",
        f"  directory : {manifest.directory}",
        f"  manifest  : {'manifest.json' if manifest.directory else ''}",
    ]
    shown = 0
    for entry in manifest.entries:
        if entry.status == "success" and shown >= limit:
            continue
        shown += 1
        lines.append("  " + entry.summary_line())
    if shown > limit:
        lines.append(f"  ... {shown - limit} more")
    lines.append("")
    lines.append("  A blocked entry is a stop, not an obstacle: the entry names the "
                 "authorised route to the resource.")
    return "\n".join(lines)
