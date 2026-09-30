"""Reading documents and archives without trusting or executing them.

The policy, stated once
-----------------------
Nothing here runs, imports, installs or interprets what it reads. A PDF is not
opened by a viewer, a macro is not run, an embedded executable is not written
out, a script is not sourced, an archive member is never extracted by
`extractall`. Every capability the file *has* is recorded as a flag, and the file
is left alone. That is the whole of §14: the tool reports what a file contains,
never what it can be made to do.

What can be read
----------------
* **PDF** — trailer metadata, the page objects, text drawn by simple content
  streams, URI links, embedded files, and the features that matter for safety
  (JavaScript, launch actions, embedded executables). The parser is shallow and
  says where it stopped: object streams from PDF 1.5+ are not decompressed, so a
  page count can be lower than what a viewer shows. It reports that rather than
  guessing.
* **ZIP and TAR** — the member list with sizes and types, traversal attempts,
  links, encrypted members, nested archives, compression ratio, and a safe
  extraction that enforces its limits member by member.
* **OOXML** — `docx`, `xlsx` and `pptx`: the text in the document part, with the
  macro part flagged and never read as code.
* **Text-ish files** — bounded and decoded with replacement, so a wrong encoding
  yields a short file rather than an exception.

Why the safe extraction is hand-written
---------------------------------------
`ZipFile.extractall` and `TarFile.extractall` both follow what the archive says.
A member named `../../etc/cron.d/x`, an absolute path, a symlink pointing outside
the destination — each is a write primitive that the archive's author chooses.
The loop here decides for itself what to create, refuses anything that resolves
outside the destination, refuses links and device nodes outright, and counts
bytes as it goes so a compression bomb cannot fill the disk before its header
lies are caught.
"""

from __future__ import annotations

import io
import os
import re
import tarfile
import zipfile
import zlib

from . import evidence as ev
from . import fetch as fetchmod

# Limits. Every one of them is enforced while reading, not after.
DEFAULT_LIMITS = {
    "max_bytes": 50_000_000,        # of the file being read
    "max_files": 500,               # archive members
    "max_total_bytes": 100_000_000,  # uncompressed total
    "max_ratio": 200,               # uncompressed / compressed
    "max_depth": 2,                 # nested archives
    "max_text_chars": 200_000,      # extracted text kept per document
    "max_pages": 500,               # PDF page objects parsed
}

EXTRACTION_STATUSES = ("not_attempted", "extracted", "partial", "refused",
                       "unsupported", "failed")

# Features that make a file worth handling carefully. None of them is an
# exploit; all of them are things a reviewer wants to know before opening it.
PDF_DANGEROUS_KEYS = {
    "/JavaScript": "an embedded JavaScript action",
    "/JS": "an embedded JavaScript action",
    "/Launch": "a launch action, which asks the viewer to run a program",
    "/EmbeddedFile": "an embedded file",
    "/OpenAction": "an automatic action when the document is opened",
    "/AA": "additional automatic actions",
    "/RichMedia": "embedded rich media",
    "/XFA": "an XFA form, which permits script in some viewers",
    "/SubmitForm": "a form submission action",
    "/GoToR": "an action that opens a remote document",
}

SHEBANG = re.compile(rb"^#!\s*/(usr/)?bin/(env\s+)?[a-z0-9_.-]+", re.I)

TRAVERSAL_MARKERS = ("..", "\\..", "/../", "..\\")


class ExtractionError(Exception):
    """Raised when a file cannot be read at all."""


def limits(**overrides):
    merged = dict(DEFAULT_LIMITS)
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


def _clip(text, limit):
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... truncated at {limit} characters"


# ------------------------------------------------------------------ the report
class Extraction:
    """What was found in one file, and what was deliberately not done."""

    def __init__(self, path, file_type, size, limits_used):
        self.path = path
        self.name = os.path.basename(path)
        self.file_type = file_type
        self.size = size
        self.limits = dict(limits_used)
        self.status = "not_attempted"
        self.sha256 = None
        self.metadata = {}
        self.text = ""
        self.text_truncated = False
        self.pages = []
        self.links = []
        self.attachments = []
        self.members = []
        self.nested = []
        self.flagged_features = []
        self.refusals = []
        self.warnings = []
        self.notes = []
        self.children = []

    @property
    def executed(self):
        """Always False. Present so a report can state it, not imply it."""
        return False

    def flag(self, what, detail):
        self.flagged_features.append({"feature": what, "detail": detail})

    def refuse(self, reason):
        self.refusals.append(reason)
        if self.status in ("not_attempted", "extracted"):
            self.status = "refused"

    def warn(self, reason):
        self.warnings.append(reason)

    def as_dict(self):
        return {
            "path": self.path,
            "name": self.name,
            "file_type": self.file_type,
            "size": self.size,
            "sha256": self.sha256,
            "status": self.status,
            "metadata": self.metadata,
            "pages_extracted": len(self.pages),
            "pages": self.pages,
            "links": self.links,
            "attachments": self.attachments,
            "members": self.members,
            "nested": self.nested,
            "flagged_features": self.flagged_features,
            "refusals": self.refusals,
            "warnings": self.warnings,
            "notes": self.notes,
            "text_chars": len(self.text),
            "text_truncated": self.text_truncated,
            "text": self.text,
            "limits": self.limits,
            "executed": False,
        }

    def summary(self):
        return {
            "name": self.name,
            "file_type": self.file_type,
            "status": self.status,
            "pages": len(self.pages),
            "members": len(self.members),
            "attachments": len(self.attachments),
            "links": len(self.links),
            "flagged_features": len(self.flagged_features),
            "refusals": len(self.refusals),
            "text_chars": len(self.text),
            "executed": False,
        }

    def report_lines(self):
        lines = [
            f"{self.name}: {self.file_type}, {self.status}",
            f"  sha256          : {self.sha256}",
        ]
        if self.pages:
            lines.append(f"  pages read      : {len(self.pages)}")
        if self.members:
            lines.append(f"  archive members : {len(self.members)}")
        if self.attachments:
            lines.append(f"  attachments     : {len(self.attachments)} (not written out)")
        if self.links:
            lines.append(f"  links           : {len(self.links)}")
        if self.flagged_features:
            lines.append(f"  flagged         : "
                         f"{', '.join(f['feature'] for f in self.flagged_features)}")
        if self.refusals:
            lines.append(f"  refused         : {'; '.join(self.refusals)}")
        if self.warnings:
            lines.append(f"  warnings        : {'; '.join(self.warnings)}")
        lines.append("  nothing was executed, imported or installed")
        return "\n".join(lines)


# ----------------------------------------------------------------------- PDF
PDF_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
PDF_OBJECT = re.compile(rb"(\d+)\s+(\d+)\s+obj(.*?)endobj", re.S)
PDF_PAGE = re.compile(rb"/Type\s*/Page[^s]")
PDF_TEXT_TOKEN = re.compile(rb"\((?:[^()\\]|\\.)*\)")
PDF_URI = re.compile(rb"/URI\s*\(([^)]*)\)")
PDF_INFO_KEYS = ("/Title", "/Author", "/Subject", "/Keywords", "/Creator",
                 "/Producer", "/CreationDate", "/ModDate")


def _pdf_string(raw):
    text = raw
    if text.startswith(b"(") and text.endswith(b")"):
        text = text[1:-1]
    if text.startswith(b"\xfe\xff"):
        try:
            return text[2:].decode("utf-16-be", errors="replace")
        except Exception:
            return ""
    for encoding in ("utf-8", "latin-1"):
        try:
            return text.decode(encoding)
        except UnicodeDecodeError:
            continue
    return text.decode("latin-1", errors="replace")


def _inflate(data):
    try:
        return zlib.decompress(data)
    except zlib.error:
        try:
            return zlib.decompressobj().decompress(data)
        except zlib.error:
            return None


def read_pdf(path, limits_used):
    """A shallow read of a PDF: what is in the file, without rendering it.

    Deliberately not a PDF engine. It finds page objects and the streams that
    hold simple text, decodes Flate-compressed streams with `zlib`, and reports
    what it could not reach. Metadata written with object streams is not read,
    and the report says so rather than presenting a short answer as complete.
    """
    report = Extraction(path, "pdf", os.path.getsize(path), limits_used)
    report.sha256 = ev.file_sha256(path)
    with open(path, "rb") as fh:
        raw = fh.read(limits_used["max_bytes"])
        complete = os.path.getsize(path) <= limits_used["max_bytes"]
    if not raw.startswith(b"%PDF-"):
        report.refuse("the file does not begin with a PDF header")
        report.warn("the extension says pdf and the bytes say otherwise")
        return report
    if not complete:
        report.refuse(f"the file is larger than the {limits_used['max_bytes']} byte limit")
        return report
    report.metadata["header"] = raw[:8].decode("latin-1", errors="replace").strip()
    report.metadata["encrypted"] = b"/Encrypt" in raw
    if report.metadata["encrypted"]:
        report.warn("the document declares encryption; its content was not decrypted")

    for key in PDF_INFO_KEYS:
        match = re.search(re.escape(key.encode()) + rb"\s*\(([^)]*)\)", raw)
        if match:
            report.metadata[key.lstrip("/").lower()] = _clip(_pdf_string(match.group(1)), 300)

    objects = PDF_OBJECT.findall(raw)
    report.metadata["objects"] = len(objects)
    page_objects = [obj for obj in objects if PDF_PAGE.search(obj[2] or b"")]
    report.metadata["page_objects"] = len(page_objects)
    if not page_objects:
        report.metadata["pages_note"] = (
            "no uncompressed page objects were found; a PDF 1.5+ file keeps them in "
            "object streams, which this reader does not decompress")

    for index, (_number, _generation, body) in enumerate(
            page_objects[:limits_used["max_pages"]]):
        page = {"index": index + 1, "media_box": None, "text_chars": 0,
                "sha256": ev.sha256_bytes(body),
                "features": []}
        box = re.search(rb"/MediaBox\s*\[([^\]]*)\]", body)
        if box:
            page["media_box"] = b" ".join(box.group(1).split()).decode("latin-1", errors="replace")
        features = [label for key, label in PDF_DANGEROUS_KEYS.items()
                    if key.encode() in body]
        if features:
            page["features"] = sorted(set(features))
        report.pages.append(page)

    # Text from the content streams, in document order, with the caveat attached:
    # this reads what a simple stream draws, not what a viewer renders.
    chunks = []
    stream_index = 0
    for stream_match in PDF_STREAM.finditer(raw):
        stream_index += 1
        payload = stream_match.group(1)
        # A stream that is not a token in a dictionary is compressed; inflate it.
        decoded = payload if payload.lstrip()[:1] in (b"(", b"[", b"/", b"B", b"T") \
            else _inflate(payload)
        if decoded is None:
            continue
        if not decoded.lstrip()[:2] in (b"BT", b"B ", b"q ", b"/"):
            continue
        for token in PDF_TEXT_TOKEN.findall(decoded):
            text = _pdf_string(token)
            if text.strip():
                chunks.append(text)
        if stream_index > 200:
            report.warn("only the first 200 streams were read")
            break
    report.text = _clip(" ".join(chunks), limits_used["max_text_chars"])
    report.text_truncated = len(report.text) >= limits_used["max_text_chars"]

    for uri in PDF_URI.findall(raw):
        url = _pdf_string(uri)
        if url and url not in report.links:
            report.links.append({"type": "uri", "target": _clip(url, 500)})

    if b"/EmbeddedFile" in raw:
        for name in re.findall(rb"/F\s*\(([^)]*)\)", raw)[:20]:
            report.attachments.append({"name": _clip(_pdf_string(name), 200),
                                       "written_out": False})
        if not report.attachments:
            report.attachments.append({"name": "(embedded stream)",
                                       "written_out": False})

    for key, label in PDF_DANGEROUS_KEYS.items():
        if key.encode() in raw:
            report.flag(label, f"{key} appears in the file")
    if report.metadata["encrypted"]:
        report.flag("encryption", "the document declares /Encrypt")
    report.notes.append(
        "read without rendering: this is not a PDF parser and does not decode every "
        "filter, so text and page counts can be incomplete")
    report.status = "partial" if report.warnings or not page_objects else "extracted"
    return report


# ------------------------------------------------------------------- archives
def _member_type(name, is_directory=False):
    """A short name for a member, from its name. `ZipInfo` and `TarInfo` disagree
    about how to ask whether something is a directory, so the caller answers."""
    if is_directory:
        return "directory"
    name = (name or "").lower()
    for extension, kind in ((".pdf", "pdf"), (".zip", "zip"), (".tar", "tar"),
                            (".gz", "gzip"), (".js", "script"), (".sh", "script"),
                            (".py", "script"), (".exe", "executable"),
                            (".dll", "executable"), (".so", "executable"),
                            (".docm", "macro_document"), (".xlsm", "macro_document"),
                            (".docx", "document"), (".xlsx", "spreadsheet")):
        if name.endswith(extension):
            return kind
    return "file"


def _unsafe_member_name(name):
    """Why this member name must not be extracted, or an empty string."""
    if not name or name in (".", "./"):
        return "an empty member name"
    normalised = name.replace("\\", "/")
    if normalised.startswith("/") or re.match(r"^[A-Za-z]:", normalised):
        return "an absolute path"
    parts = [part for part in normalised.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        return "a path that climbs out of the destination"
    if "\x00" in name:
        return "a null byte in the name"
    return ""


def _resolve_inside(destination, name):
    target = os.path.realpath(os.path.join(destination, name))
    root = os.path.realpath(destination)
    return target == root or target.startswith(root + os.sep)


def read_zip(path, limits_used, depth=0, root=None):
    report = Extraction(path, "zip", os.path.getsize(path), limits_used)
    report.sha256 = ev.file_sha256(path)
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        report.status = "failed"
        report.refuse(f"not a readable zip: {type(exc).__name__}: {exc}")
        return report
    with archive:
        infos = archive.infolist()
        report.metadata["members_declared"] = len(infos)
        if len(infos) > limits_used["max_files"]:
            report.refuse(f"more than {limits_used['max_files']} members "
                          f"({len(infos)}); the archive was listed and not read")
            report.status = "refused"
            for info in infos[:50]:
                report.members.append({"name": _clip(info.filename, 200), "size": info.file_size,
                                       "type": _member_type(info.filename, info.is_dir()),
                                       "read": False})
            report.warn("listing is partial: the first 50 names are shown")
            return report
        total = 0
        for info in infos:
            member = {
                "name": _clip(info.filename, 300),
                "size": info.file_size,
                "compressed": info.compress_size,
                "type": _member_type(info.filename, info.is_dir()),
                "encrypted": bool(info.flag_bits & 0x1),
                "is_link": False,
                "read": True,
            }
            unsafe = _unsafe_member_name(info.filename)
            if unsafe:
                member["unsafe"] = unsafe
                report.refuse(f"member {info.filename!r}: {unsafe}")
            if member["encrypted"]:
                report.warn(f"member {info.filename!r} is encrypted; no password was tried")
                report.flag("encrypted member", info.filename)
            total += info.file_size
            report.members.append(member)
        report.metadata["uncompressed_total"] = total
        compressed = max(1, os.path.getsize(path))
        report.metadata["ratio"] = round(total / compressed, 2)
        if total > limits_used["max_total_bytes"]:
            report.refuse(f"uncompressed content exceeds {limits_used['max_total_bytes']} "
                          f"bytes ({total}); nothing was extracted")
            report.status = "refused"
            return report
        if report.metadata["ratio"] > limits_used["max_ratio"]:
            report.refuse(f"compression ratio {report.metadata['ratio']}:1 exceeds the "
                          f"{limits_used['max_ratio']}:1 limit; treated as a "
                          f"decompression bomb and not extracted")
            report.status = "refused"
            return report
        if b"vbaProject" in b"".join(i.filename.encode("utf-8", "replace")
                                     for i in infos):
            report.flag("macro part", "the archive contains a VBA project part")
        report.status = "listed"
    if depth < limits_used["max_depth"]:
        report.nested = _look_inside(path, report, limits_used, depth, root=root)
    return report


def read_tar(path, limits_used, depth=0, root=None):
    report = Extraction(path, "tar", os.path.getsize(path), limits_used)
    report.sha256 = ev.file_sha256(path)
    try:
        archive = tarfile.open(path, "r:*")
    except (tarfile.TarError, OSError) as exc:
        report.status = "failed"
        report.refuse(f"not a readable tar: {type(exc).__name__}: {exc}")
        return report
    with archive:
        try:
            members = archive.getmembers()
        except tarfile.TarError as exc:
            report.status = "failed"
            report.refuse(f"the member list could not be read: {exc}")
            return report
        report.metadata["members_declared"] = len(members)
        if len(members) > limits_used["max_files"]:
            report.refuse(f"more than {limits_used['max_files']} members ({len(members)})")
            report.status = "refused"
            return report
        total = 0
        for info in members:
            entry = {
                "name": _clip(info.name, 300),
                "size": info.size,
                "type": "link" if (info.issym() or info.islnk()) else
                        ("device" if (info.ischr() or info.isblk() or info.isfifo()) else
                         _member_type(info.name, info.isdir())),
                "is_link": bool(info.issym() or info.islnk()),
                "linkname": _clip(getattr(info, "linkname", "") or "", 200),
                "read": True,
            }
            unsafe = _unsafe_member_name(info.name)
            if unsafe:
                entry["unsafe"] = unsafe
            if entry["is_link"]:
                report.refuse(f"member {info.name!r} is a link to {entry['linkname']!r}; "
                              f"links are never extracted")
            elif entry["type"] == "device":
                report.refuse(f"member {info.name!r} is a device or fifo; not extracted")
            elif unsafe:
                report.refuse(f"member {info.name!r}: {unsafe}")
            total += info.size
            report.members.append(entry)
        report.metadata["uncompressed_total"] = total
        ratio = total / max(1, os.path.getsize(path))
        report.metadata["ratio"] = round(ratio, 2)
        if total > limits_used["max_total_bytes"]:
            report.refuse(f"uncompressed content exceeds {limits_used['max_total_bytes']} bytes")
            report.status = "refused"
            return report
        if ratio > limits_used["max_ratio"]:
            report.refuse(f"compression ratio {ratio:.0f}:1 exceeds the limit; "
                          f"treated as a decompression bomb and not extracted")
            report.status = "refused"
            return report
        report.status = "listed"
    if depth < limits_used["max_depth"]:
        report.nested = _look_inside(path, report, limits_used, depth, root=root)
    return report


def _look_inside(path, report, limits_used, depth, root=None):
    """Detect archives inside an archive, and read them one level in.

    Members are read into memory and bounded, so a nested archive is analysed
    without ever being written to disk. Nested extraction is where traversal and
    bomb problems compound, which is why the depth is capped and why the report
    names the parent for every child.
    """
    children = []
    try:
        if path.lower().endswith((".zip", ".docx", ".xlsx", ".pptx", ".jar", ".epub")):
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if info.file_size == 0 or info.compress_size == 0:
                        continue
                    if _member_type(info.filename, info.is_dir()) != "zip" and \
                            not info.filename.lower().endswith(
                                (".zip", ".gz", ".tgz", ".tar.gz")):
                        continue
                    if info.file_size > limits_used["max_bytes"]:
                        report.warn(f"nested archive {info.filename!r} is larger than the "
                                    f"size limit and was not read")
                        continue
                    try:
                        data = archive.read(info)
                    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
                        report.warn(f"nested archive {info.filename!r} could not be read: {exc}")
                        continue
                    children.append(_read_nested_bytes(
                        data, f"{report.name}!{info.filename}", limits_used, depth + 1))
    except (zipfile.BadZipFile, OSError):
        return []
    return [child for child in children if child is not None]


def _read_nested_bytes(data, name, limits_used, depth):
    """Read a nested archive from bytes, never from disk."""
    if not data:
        return None
    if data[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as nested:
                names = nested.namelist()
                report = Extraction(name, "zip", len(data), limits_used)
                report.metadata["members_declared"] = len(names)
                report.metadata["nested_from"] = name.split("!", 1)[0]
                report.status = "listed"
                for member in names[:100]:
                    unsafe = _unsafe_member_name(member)
                    if unsafe:
                        report.refuse(f"member {member!r}: {unsafe}")
                    report.members.append({"name": _clip(member, 300), "type": "unknown",
                                           "read": False, "unsafe": unsafe or None})
                if len(names) > 100:
                    report.warn(f"listing is partial: {len(names) - 100} more members")
                return report
        except zipfile.BadZipFile as exc:
            report = Extraction(name, "zip", len(data), limits_used)
            report.status = "failed"
            report.refuse(f"nested archive could not be read: {exc}")
            return report
    if data[:2] == b"\x1f\x8b":
        try:
            inflated = zlib.decompress(data, 16 + zlib.MAX_WBITS)
        except zlib.error as exc:
            report = Extraction(name, "gzip", len(data), limits_used)
            report.status = "failed"
            report.refuse(f"gzip member could not be decompressed: {exc}")
            return report
        if len(inflated) > limits_used["max_total_bytes"]:
            report = Extraction(name, "gzip", len(data), limits_used)
            report.status = "refused"
            report.refuse("the compressed member inflates past the total-size limit")
            return report
        report = Extraction(name, "gzip", len(data), limits_used)
        report.metadata["uncompressed_bytes"] = len(inflated)
        report.metadata["nested_from"] = name.split("!", 1)[0]
        report.notes.append("decompressed in memory for inspection only; not written out")
        if inflated[:2] == b"PK":
            report.children = [child for child in
                               [_read_nested_bytes(inflated, f"{name}!inner.zip",
                                                   limits_used, depth + 1)] if child]
        report.status = "listed"
        return report
    return None


def extract_archive(path, destination, limits_used, report=None):
    """Extract members this code has vetted itself. Never `extractall`.

    Returns the list of written files. Anything with an unsafe name, a link, a
    device node, an encrypted payload or a size past the limits is skipped and
    the reason is recorded on the report.
    """
    report = report or read_zip(path, limits_used)
    written = []
    skipped = 0
    if report.status == "refused" or report.sha256 is None:
        return written
    os.makedirs(destination, exist_ok=True)
    total = 0
    count = 0
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        report.warn(f"extraction refused: {exc}")
        return written
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if count >= limits_used["max_files"]:
                report.warn("extraction stopped at the member limit")
                break
            unsafe = _unsafe_member_name(info.filename)
            if unsafe or (info.flag_bits & 0x1):
                report.warn(f"skipped {info.filename!r}: "
                            f"{unsafe or 'encrypted member'}")
                skipped += 1
                continue
            if not _resolve_inside(destination, info.filename):
                report.warn(f"skipped {info.filename!r}: resolves outside the destination")
                skipped += 1
                continue
            total += info.file_size
            if total > limits_used["max_total_bytes"]:
                report.warn("extraction stopped at the total-size limit")
                skipped += 1
                break
            target = os.path.join(destination, info.filename)
            os.makedirs(os.path.dirname(target) or destination, exist_ok=True)
            try:
                with archive.open(info) as source, open(target, "wb") as sink:
                    copied = 0
                    while True:
                        chunk = source.read(65536)
                        if not chunk:
                            break
                        copied += len(chunk)
                        if copied > limits_used["max_bytes"]:
                            raise ExtractionError("member larger than the per-file limit")
                        sink.write(chunk)
            except (OSError, ExtractionError, zipfile.BadZipFile, RuntimeError) as exc:
                report.warn(f"skipped {info.filename!r}: {exc}")
                if os.path.exists(target):
                    os.remove(target)
                skipped += 1
                continue
            written.append(target)
            count += 1
    # A run that wrote some members and skipped others is a partial extraction,
    # and saying "extracted" would hide the members that were left behind.
    if skipped and written:
        report.status = "partial"
    elif skipped and not written:
        report.status = "refused"
    elif written:
        report.status = "extracted"
    return written


def extract_tar_archive(path, destination, limits_used, report=None):
    """The same rules as the zip path, for tar. Links and devices are never written.

    `TarFile.extractall` follows a member's own idea of where it should go, which
    is why this walks the members itself: a name that climbs out, a symlink
    pointing at `/etc`, a character device — each is a write primitive the
    archive's author chooses, and each is refused here.
    """
    report = report or read_tar(path, limits_used)
    written = []
    skipped = 0
    if report.status == "refused" or report.sha256 is None:
        return written
    os.makedirs(destination, exist_ok=True)
    try:
        archive = tarfile.open(path, "r:*")
    except (tarfile.TarError, OSError) as exc:
        report.warn(f"extraction refused: {exc}")
        return written
    total = 0
    with archive:
        for info in archive.getmembers():
            if info.isdir():
                continue
            if len(written) >= limits_used["max_files"]:
                report.warn("extraction stopped at the member limit")
                skipped += 1
                break
            reason = ""
            if info.issym() or info.islnk():
                reason = f"a link to {info.linkname!r}"
            elif info.ischr() or info.isblk() or info.isfifo():
                reason = "a device or fifo"
            else:
                reason = _unsafe_member_name(info.name)
            if reason or not _resolve_inside(destination, info.name):
                report.warn(f"skipped {info.name!r}: {reason or 'resolves outside the destination'}")
                skipped += 1
                continue
            total += info.size
            if total > limits_used["max_total_bytes"]:
                report.warn("extraction stopped at the total-size limit")
                skipped += 1
                break
            target = os.path.join(destination, info.name)
            os.makedirs(os.path.dirname(target) or destination, exist_ok=True)
            source = archive.extractfile(info)
            if source is None:
                report.warn(f"skipped {info.name!r}: no readable content")
                skipped += 1
                continue
            try:
                with source, open(target, "wb") as sink:
                    copied = 0
                    while True:
                        chunk = source.read(65536)
                        if not chunk:
                            break
                        copied += len(chunk)
                        if copied > limits_used["max_bytes"]:
                            raise ExtractionError("member larger than the per-file limit")
                        sink.write(chunk)
            except (OSError, ExtractionError, tarfile.TarError) as exc:
                report.warn(f"skipped {info.name!r}: {exc}")
                if os.path.exists(target):
                    os.remove(target)
                skipped += 1
                continue
            written.append(target)
    if skipped and written:
        report.status = "partial"
    elif skipped and not written:
        report.status = "refused"
    elif written:
        report.status = "extracted"
    return written


# --------------------------------------------------------------------- OOXML
# The macro-enabled variants are included deliberately: those are the packages
# where the macro part matters, so they must reach the reader that flags it
# rather than the generic archive reader.
OOXML_EXTENSIONS = (".docx", ".docm", ".xlsx", ".xlsm", ".pptx", ".pptm")
OOXML_TEXT_PARTS = {
    "docx": ("word/document.xml",), "docm": ("word/document.xml",),
    "xlsx": ("xl/sharedStrings.xml",), "xlsm": ("xl/sharedStrings.xml",),
    "pptx": ("ppt/slides/slide1.xml",), "pptm": ("ppt/slides/slide1.xml",),
}
XML_TEXT = re.compile(rb"<[^>]+>")


def read_ooxml(path, limits_used):
    """Text from an Office document, and the macro part flagged untouched."""
    report = Extraction(path, os.path.splitext(path)[1].lstrip("."), os.path.getsize(path),
                        limits_used)
    report.sha256 = ev.file_sha256(path)
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        report.status = "failed"
        report.refuse(f"not a readable package: {exc}")
        return report
    with archive:
        names = archive.namelist()
        report.metadata["parts"] = len(names)
        for name in names:
            lowered = name.lower()
            if "vbaproject" in lowered or lowered.endswith(".bin") and "macro" in lowered:
                report.flag("macro part", f"{name} is present and was not read")
            if lowered.endswith((".exe", ".dll", ".scr", ".js", ".vbs", ".ps1")):
                report.flag("embedded executable or script", name)
                report.attachments.append({"name": name, "written_out": False})
        parts = OOXML_TEXT_PARTS.get(report.file_type, ())
        chunks = []
        for part in parts:
            if part not in names:
                continue
            try:
                data = archive.read(part)
            except (zipfile.BadZipFile, RuntimeError, KeyError) as exc:
                report.warn(f"{part} could not be read: {exc}")
                continue
            text = XML_TEXT.sub(b" ", data)
            chunks.append(text.decode("utf-8", errors="replace"))
        report.text = _clip(" ".join(chunks), limits_used["max_text_chars"])
        report.text_truncated = len(report.text) >= limits_used["max_text_chars"]
        report.metadata["text_parts"] = [p for p in parts if p in names]
    report.notes.append("read as a package: no macro, script or embedded object was run")
    report.status = "extracted" if report.text else "partial"
    return report


# ---------------------------------------------------------------------- text
def read_text(path, limits_used):
    report = Extraction(path, "text", os.path.getsize(path), limits_used)
    report.sha256 = ev.file_sha256(path)
    with open(path, "rb") as fh:
        data = fh.read(limits_used["max_bytes"])
    report.text = _clip(data.decode("utf-8", errors="replace"),
                        limits_used["max_text_chars"])
    report.text_truncated = len(report.text) >= limits_used["max_text_chars"]
    report.status = "extracted"
    return report


# ----------------------------------------------------------------- protection
def static_flags(path, file_type=None):
    """What a file *is*, recorded as flags. Nothing is run.

    Returns a list of `{"feature", "detail"}`. Executable content is a fact about
    the file, and a reviewer wants it before opening it; the tool reports the
    fact and does not act on it.
    """
    flags = []
    with open(path, "rb") as fh:
        prefix = fh.read(4096)
    file_type = file_type or fetchmod.sniff_type(prefix, "", path)[0]
    if prefix[:1] == b"\x7f" and prefix[:4] == b"\x7fELF":
        flags.append({"feature": "ELF executable", "detail": "a Linux binary"})
    elif prefix[:2] == b"MZ":
        flags.append({"feature": "PE executable", "detail": "a Windows binary"})
    elif prefix[:4] == b"\xca\xfe\xba\xbe":
        flags.append({"feature": "Mach-O or Java class", "detail": "a compiled binary"})
    if SHEBANG.match(prefix):
        flags.append({"feature": "script with a shebang",
                      "detail": "a file that a shell would run if invoked"})
    if file_type == "ole":
        flags.append({"feature": "OLE compound document",
                      "detail": "the legacy container that often carries macros"})
    return flags


def extension_mismatch(path, file_type):
    """Whether the extension describes something other than the bytes."""
    extension = os.path.splitext(path)[1].lower()
    expected = fetchmod.EXTENSION_TYPES.get(extension)
    if expected is None or file_type in (None, "unknown"):
        return None
    return expected != file_type


def quarantine(path, quarantine_dir):
    """Move a file aside, keeping its name and a note of where it came from."""
    os.makedirs(quarantine_dir, exist_ok=True)
    target = os.path.join(quarantine_dir, os.path.basename(path))
    if os.path.exists(target):
        stem, extension = os.path.splitext(os.path.basename(path))
        counter = 2
        while os.path.exists(target):
            target = os.path.join(quarantine_dir, f"{stem}-{counter}{extension}")
            counter += 1
    os.rename(path, target)
    with open(target + ".origin", "w", encoding="utf-8") as fh:
        fh.write(f"quarantined from: {path}\nquarantined_at: {fetchmod.now()}\n")
    return target


# ------------------------------------------------------------------- dispatch
def inspect_file(path, limits_used=None, *, extract_into=None, file_type=None,
                 quarantine_dir=None):
    """Read one file according to what it is, and record what was not read."""
    limits_used = limits_used or limits()
    if not os.path.isfile(path):
        report = Extraction(path, "unknown", 0, limits_used)
        report.status = "failed"
        report.refuse("no such file")
        return report
    with open(path, "rb") as fh:
        prefix = fh.read(64)
    detected, confident = fetchmod.sniff_type(prefix, "", path)
    declared = file_type or detected
    report_type = declared
    if declared == "pdf":
        report = read_pdf(path, limits_used)
    elif declared in ("zip", "ole") or os.path.splitext(path)[1].lower() in (
            OOXML_EXTENSIONS + (".epub", ".jar")):
        extension = os.path.splitext(path)[1].lower()
        if extension in OOXML_EXTENSIONS:
            report = read_ooxml(path, limits_used)
        else:
            report = read_zip(path, limits_used)
    elif declared == "gzip" or os.path.splitext(path)[1].lower() in (".tar", ".tgz"):
        report = read_tar(path, limits_used)
    elif declared in ("text", "json", "html", "csv", "unknown") or not confident:
        report = read_text(path, limits_used)
    else:
        report = Extraction(path, report_type, os.path.getsize(path), limits_used)
        report.sha256 = ev.file_sha256(path)
        report.status = "unsupported"
        report.notes.append(f"{report_type} content is recorded but not parsed")

    # Compared against the detected type whether or not a magic number produced
    # it: a `.pdf` holding an HTML login page is the case this exists for, and
    # gating the check on confidence meant it was never flagged.
    mismatch = extension_mismatch(path, detected)
    if mismatch:
        report.flag("extension does not match the content",
                    f"the name says {os.path.splitext(path)[1]} and the bytes are {detected}")
        report.warn("the file name describes something other than the content")
    for flag in static_flags(path, detected):
        report.flag(flag["feature"], flag["detail"])
    if quarantine_dir and (mismatch or any(
            f["feature"].endswith("executable") for f in report.flagged_features)):
        report.notes.append(f"the file was moved to {quarantine_dir} rather than left in place")
        report.quarantined_to = quarantine(path, quarantine_dir)

    if extract_into and report.status in ("listed", "extracted", "partial"):
        written = []
        if report.file_type == "zip":
            written = extract_archive(path, extract_into, limits_used, report)
        elif report.file_type == "tar":
            written = extract_tar_archive(path, extract_into, limits_used, report)
        if report.file_type in ("zip", "tar"):
            report.notes.append(f"{len(written)} member(s) extracted to {extract_into}")
    if extract_into and report.file_type in [e.lstrip(".") for e in OOXML_EXTENSIONS]:
        report.notes.append("an Office document is read in place; its parts are not unpacked")
    return report


def extraction_status(report):
    """The value that goes into a manifest entry's `extraction_status` field."""
    mapping = {
        "extracted": "extracted",
        "partial": "extracted_with_caveats",
        "listed": "listed_not_extracted",
        "refused": "refused",
        "unsupported": "unsupported",
        "failed": "failed",
        "not_attempted": "not_attempted",
    }
    return mapping.get(report.status, "not_attempted")
