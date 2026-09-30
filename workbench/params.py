"""Parameter discovery and classification.

Where inputs live
-----------------
Every place a request carries a value the target will interpret: the query
string, path segments, form fields, JSON fields (including nested paths),
multipart parts, cookies and custom headers.

Why classification, not a wordlist
----------------------------------
The point of classifying a parameter is to decide which *kind* of variation is
worth trying, and that depends on what the parameter appears to be. A `page`
parameter invites boundary values (0, -1, a very large number); a `file`
parameter invites a content-type and filename check; an opaque identifier
invites asking whether the same object is returned to a second authorized
identity. Guessing from a list of famous names produces noise; reading the value
the operator already has produces a test worth running.

Value handling
--------------
Values are captured as short previews, and the preview of anything whose name
looks like a credential is replaced with a marker. A parameter inventory is
still an artifact that gets attached to a report, so it follows the same rule as
everything else that gets attached to a report.

Nothing in this module sends a request. It reads what was already captured.
"""

from __future__ import annotations

import json
import re
import urllib.parse

# Names whose values are masked in any output this module produces.
SENSITIVE_NAME = re.compile(
    r"(pass|pwd|secret|token|api[_-]?key|auth|session|csrf|xsrf|otp|pin|"
    r"signature|sig|credential|private)", re.I)

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
HEX_RE = re.compile(r"^[0-9a-f]{16,64}$", re.I)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$", re.I)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)

CATEGORY_NAMES = {
    "search": {"q", "query", "search", "s", "term", "keyword", "keywords", "find"},
    "pagination": {"page", "p", "offset", "limit", "per_page", "perpage", "size",
                   "cursor", "start", "count", "skip", "top", "from"},
    "sorting": {"sort", "order", "sort_by", "order_by", "direction", "dir", "asc",
                "desc", "orderby", "sortby"},
    "filter": {"filter", "where", "category", "type", "status", "tag", "tags",
               "state", "role", "scope", "kind", "group", "level"},
    "file": {"file", "upload", "attachment", "document", "doc", "image", "avatar",
             "photo", "filename", "path", "template"},
}

MASK = "[masked]"


def mask_value(name, value):
    """Mask the preview of a value whose name suggests a credential."""
    if value is None:
        return None
    if SENSITIVE_NAME.search(name or ""):
        return MASK
    text = str(value)
    return text if len(text) <= 120 else text[:117] + "..."


class Parameter:
    """One input the target reads, wherever it lives."""

    def __init__(self, location, name, value, *, indexed=False, note="", path=""):
        self.location = location
        self.name = name
        self.value = "" if value is None else str(value)
        self.indexed = indexed
        self.note = note
        self.path = path
        self.category = classify(self.name, self.value, location)

    def as_dict(self):
        return {
            "location": self.location,
            "name": self.name,
            "path": self.path or self.name,
            "value_preview": mask_value(self.name, self.value),
            "category": self.category,
            "indexed": self.indexed,
            "note": self.note,
        }

    def __repr__(self):
        return f"<Parameter {self.location}:{self.name}={mask_value(self.name, self.value)}>"


def classify(name, value, location="query"):
    """Classify a parameter from its name and value.

    Ordered from the most specific signal to the least: a value that is
    unmistakably an identifier is one even if the name is vague, and a name in a
    known vocabulary wins over a generic value shape.
    """
    lowered = (name or "").lower()
    value = "" if value is None else str(value)

    if location == "path":
        if value.isdigit():
            return "identifier"
        if UUID_RE.match(value) or HEX_RE.match(value):
            return "identifier"
        return "path-segment"
    if lowered in CATEGORY_NAMES["search"]:
        return "search"
    if lowered in CATEGORY_NAMES["pagination"]:
        return "pagination"
    if lowered in CATEGORY_NAMES["sorting"]:
        return "sorting"
    if lowered in CATEGORY_NAMES["filter"]:
        return "filter"
    if lowered in CATEGORY_NAMES["file"]:
        return "file"
    # A word-boundary match, not `endswith("id")`: that would classify "valid"
    # and "paid" as identifiers, which is the kind of quiet wrongness that sends
    # a fuzzing budget at the wrong parameter.
    if re.search(r"(?:^|_)id$", lowered) or re.search(r"(?:^|_)(uuid|guid|key)$", lowered):
        return "identifier"
    if UUID_RE.match(value) or HEX_RE.match(value):
        return "identifier"
    if value.lower() in ("true", "false", "yes", "no", "on", "off"):
        return "boolean"
    if re.fullmatch(r"-?\d+", value):
        return "numeric"
    if re.fullmatch(r"-?\d+\.\d+", value):
        return "numeric"
    if value.startswith(("http://", "https://", "//")):
        return "url"
    if value.startswith("/") and len(value) > 1:
        return "url"
    if EMAIL_RE.match(value):
        return "email"
    if SLUG_RE.match(value):
        return "slug"
    if "=" in value and "&" in value:
        return "encoded"
    return "unknown"


# ---------------------------------------------------------------- extraction
def from_url(url):
    """Query parameters, plus path segments that look like values."""
    out = []
    parsed = urllib.parse.urlsplit(url or "")
    for name, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        out.append(Parameter("query", name, value))
    segments = [s for s in (parsed.path or "").split("/") if s]
    for index, segment in enumerate(segments):
        # A segment that is not a static word is a value the target reads.
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", segment) and segment.lower() in (
                "api", "v1", "v2", "v3", "rest", "graphql", "admin", "user",
                "users", "account", "item", "items", "search", "static"):
            continue
        if re.search(r"\d", segment) or UUID_RE.match(segment) or "-" in segment:
            out.append(Parameter("path", f"segment[{index}]", segment, indexed=True,
                                 note=f"path position {index}"))
    return out


def from_body(body_text, content_type=""):
    """Form fields, JSON fields, or multipart parts, depending on content type."""
    content_type = (content_type or "").split(";")[0].strip().lower()
    if content_type == "multipart/form-data":
        return _from_multipart(body_text, content_type)
    if content_type == "application/x-www-form-urlencoded" or (
            not content_type and "=" in (body_text or "") and "{" not in (body_text or "")[:1]):
        return [Parameter("form", name, value)
                for name, value in urllib.parse.parse_qsl(body_text or "",
                                                          keep_blank_values=True)]
    if content_type == "application/json" or (body_text or "").lstrip()[:1] in "{[":
        return _from_json(body_text)
    return []


def _from_json(body_text):
    try:
        data = json.loads(body_text or "null")
    except (json.JSONDecodeError, TypeError):
        return []
    out = []

    def walk(node, path):
        if isinstance(node, dict):
            for key in node:
                walk(node[key], f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for i, item in enumerate(node[:20]):
                walk(item, f"{path}[{i}]")
        else:
            name = path.split(".")[-1].split("[")[0]
            out.append(Parameter("json", name, node, indexed="[" in path, path=path))

    walk(data, "")
    return out


def _from_multipart(body_text, content_type):
    """Multipart part names and metadata, without parsing file content.

    Only the disposition headers are read: a fixture-size parser that decodes
    arbitrary file parts is a parser for a format an attacker chooses, and the
    metadata is what the workbench needs.
    """
    out = []
    parts = re.split(r"\r?\n--", body_text or "")
    for part in parts:
        header_block = part.split("\r\n\r\n", 1)[0].split("\n\n", 1)[0]
        name_match = re.search(r'name="([^"]*)"', header_block)
        file_match = re.search(r'filename="([^"]*)"', header_block)
        type_match = re.search(r"Content-Type:\s*([^\s;]+)", header_block, re.I)
        if not name_match:
            continue
        name = name_match.group(1)
        note = ""
        if file_match:
            note = f"file part, filename {file_match.group(1)!r}"
        elif type_match:
            note = f"part content-type {type_match.group(1)}"
        value = file_match.group(1) if file_match else (type_match.group(1) if type_match else "")
        out.append(Parameter("multipart", name, value, note=note))
    return out


def from_headers(headers):
    """Custom headers, excluding the ones that are transport or credential plumbing."""
    skip = {"host", "accept", "accept-encoding", "accept-language", "connection",
            "content-length", "content-type", "user-agent", "authorization",
            "cookie", "referer", "origin", "proxy-authorization"}
    out = []
    for name, value in (headers or {}).items():
        if name.lower() in skip:
            continue
        out.append(Parameter("header", name, value))
    return out


def from_cookies(headers):
    """Cookie names only. Values are masked by the same rule as everything else."""
    out = []
    raw = [v for k, v in (headers or {}).items() if k.lower() == "cookie"]
    for header in raw:
        for pair in str(header).split(";"):
            if "=" not in pair:
                continue
            name, value = pair.split("=", 1)
            out.append(Parameter("cookie", name.strip(), value.strip()))
    return out


def inventory(record):
    """Every parameter in a stored request record, classified."""
    request = record if "request_headers" in record else (record or {})
    url = request.get("url") or ""
    headers = request.get("request_headers") or {}
    body_text = request.get("request_body") or ""
    content_type = ""
    for name, value in headers.items():
        if name.lower() == "content-type":
            content_type = value
    params = (from_url(url) + from_body(body_text, content_type)
              + from_headers(headers) + from_cookies(headers))
    return [p.as_dict() for p in params]


def summarise(parameters):
    counts = {}
    for param in parameters:
        counts[param["category"]] = counts.get(param["category"], 0) + 1
    return {"total": len(parameters), "by_category": counts,
            "by_location": _count_by(parameters, "location")}


def _count_by(items, key):
    counts = {}
    for item in items:
        counts[item[key]] = counts.get(item[key], 0) + 1
    return counts


# ------------------------------------------------------------------- cases
# Boundary and shape cases per category. These are structural: they ask "what
# does this endpoint do with an empty value, a negative number, an unexpected
# type", which is how input handling is actually assessed. None of them are
# filter-evasion strings, and none of them are exploit payloads: the workbench
# produces candidates for an operator to send through the scope gate, not an
# attack to run at a target.
CASES = {
    "numeric": [("zero", "0"), ("negative", "-1"), ("large", "2147483648"),
                ("float", "1.5"), ("non-numeric", "abc")],
    "pagination": [("page-zero", "0"), ("negative-page", "-1"),
                   ("huge-page", "1000000"), ("non-numeric", "abc")],
    "boolean": [("flip", None), ("invalid", "maybe")],
    "sorting": [("unknown-field", "zzz"), ("injection-shaped", "name;id"),
                ("descending", "-name")],
    "search": [("empty", ""), ("unicode", "\u00e9\u00e8\u00ea"),
               ("wildcard-chars", "%_")],
    "identifier": [("zero", "0"), ("one", "1"), ("non-numeric", "abc"),
                   ("very-long", "1" * 40)],
    "url": [("relative", "/"), ("backslash", "/\\"), ("dot-segments", "/../")],
    "file": [("empty-name", ""), ("double-extension", "x.txt.png"),
             ("unicode-name", "\u00e9.txt")],
    "filter": [("empty", ""), ("duplicate", None), ("unknown-value", "zzz")],
    "email": [("invalid", "not-an-email"), ("long", "a" * 40 + "@example.test")],
    "slug": [("empty", ""), ("unicode", "\u00e9")],
    "unknown": [("empty", ""), ("long", "A" * 1000), ("unicode", "\u4e2d\u6587")],
}


def suggested_cases(parameter):
    """Case descriptors for one parameter. Sending them is `fuzz`'s decision."""
    cases = list(CASES.get(parameter["category"], CASES["unknown"]))
    out = []
    for label, value in cases:
        if value is None and label == "flip":
            current = parameter.get("value_preview") or ""
            if current == MASK:
                continue                     # never echo a masked value back
            value = "false" if current.lower() in ("true", "1", "yes", "on") else "true"
        elif value is None and label == "duplicate":
            value = "duplicate-value"
        out.append({"case": label, "value": value,
                    "category": parameter["category"],
                    "location": parameter["location"],
                    "path": parameter["path"]})
    return out


def case_matrix(parameters, budget=None):
    """Cases for a whole inventory, optionally capped.

    The cap is applied round-robin across parameters, so a budget of ten covers
    ten parameters once each rather than testing the first parameter ten times —
    coverage of the surface is worth more than depth on one input.
    """
    per_param = [suggested_cases(p) for p in parameters]
    if budget is None:
        return [case for group in per_param for case in group]
    out = []
    index = 0
    while len(out) < budget and any(group for group in per_param):
        for group in per_param:
            if group and len(out) < budget:
                out.append(group.pop(0))
        index += 1
        if index > 10000:
            break
    return out
