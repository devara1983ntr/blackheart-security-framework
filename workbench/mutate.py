"""Safe request mutation.

What a mutation is here
-----------------------
A single, named, reversible change to one part of a request: one header added,
one value replaced, one field's type changed. The catalogue is deliberately
structural. It asks how an endpoint handles an empty value, a duplicate key, a
negative number, a normalised or decomposed string, a declared content type that
does not match the body — questions whose answers are about input handling.

What a mutation is not
----------------------
It is not a payload. There is no filter-evasion string in this module, no
encoding chosen to slip past a WAF, no marker that only an attacker would send.
The reason is not squeamishness: evasion strings make a test non-reproducible
(the result depends on an intermediary's rule set, which is not the target's
behaviour), and the workbench has no way to distinguish "the target rejected it"
from "something in the middle did". A mutation here is a request the target's
own specification permits, sent with a value its author probably did not expect.

Every mutation is recorded as a description — kind, target, what it was, what it
became — so a finding can name the exact request that produced it, and so a
mutation that turns out to be interesting can be replayed by hand.
"""

from __future__ import annotations

import json
import unicodedata
import urllib.parse

KINDS = ("header", "query", "json", "form", "cookie", "method", "encoding",
         "content-type")


class Mutation:
    """One described change. Immutable: producing a mutated request is a copy."""

    def __init__(self, kind, target, before, after, note="", mode="replace"):
        self.kind = kind
        self.target = target
        self.before = before
        self.after = after
        self.note = note
        # "replace" rewrites the existing value, "append" adds a second copy of
        # the same name, "add" introduces a name that was not there. Stated
        # explicitly rather than inferred at apply time: a duplicate-parameter
        # case that turns out to be a silent replacement is a test that never
        # ran and a result that looks like it did.
        self.mode = mode

    def as_dict(self):
        return {"kind": self.kind, "target": self.target, "mode": self.mode,
                "before": _short(self.before), "after": _short(self.after),
                "note": self.note}

    def __repr__(self):
        return f"<Mutation {self.kind}:{self.target} {_short(self.before)} -> {_short(self.after)}>"


def _short(value, limit=120):
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _clone(record):
    return {
        "url": record.get("url") or "",
        "method": (record.get("method") or "GET").upper(),
        "headers": dict(record.get("request_headers") or {}),
        "body": record.get("request_body") or "",
    }


def _reencode(url, pairs):
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.urlencode(pairs, doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                                    query, parsed.fragment))


# ---------------------------------------------------------------- catalogue
def header_mutations(record):
    """Header-level mutations, excluding the sensitive ones by name.

    `Authorization` and `Cookie` are not mutated: changing them changes *whose*
    request this is, which is an identity question that belongs to the two-pair
    authorization test, not to a generic sweep.
    """
    base = _clone(record)
    out = []
    for name in base["headers"]:
        if name.lower() in ("authorization", "cookie", "proxy-authorization"):
            continue
        out.append(Mutation("header", name, base["headers"][name], "",
                            "same header, empty value"))
        out.append(Mutation("header", name, base["headers"][name],
                            base["headers"][name] + ", " + base["headers"][name],
                            "same header, value duplicated"))
    if "X-Blackheart-Probe" not in base["headers"]:
        out.append(Mutation("header", "X-Blackheart-Probe", None, "1",
                            "a header the endpoint does not document"))
    return out


def query_mutations(record):
    """Query-string mutations: empty, duplicate, boundary, ordering."""
    base = _clone(record)
    parsed = urllib.parse.urlsplit(base["url"])
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    out = []
    for name, value in pairs:
        out.append(Mutation("query", name, value, "", "empty value"))
        out.append(Mutation("query", name, value, value + value, "value repeated"))
        out.append(Mutation("query", name, value, value + "'", "quote appended"))
    if pairs:
        name, value = pairs[0]
        out.append(Mutation("query", name, value, "second-value", "the same parameter sent twice "
                            "with different values", mode="append"))
    else:
        out.append(Mutation("query", "x", None, "1", "an undocumented parameter",
                            mode="add"))
    return out


def encoding_mutations(record):
    """Unicode normalisation and percent-encoding differences.

    These test whether the target normalises before it compares. That is a
    question about the target's input handling, which is a legitimate thing to
    ask of a system you are authorised to test; it is not an attempt to defeat a
    filter, and none of these values is chosen to be rejected by one.
    """
    base = _clone(record)
    parsed = urllib.parse.urlsplit(base["url"])
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    out = []
    sample = pairs[0] if pairs else ("q", "test")
    name, value = sample
    composed = unicodedata.normalize("NFC", value or "")
    decomposed = unicodedata.normalize("NFD", value or "")
    out.append(Mutation("encoding", name, value, composed,
                        "the same value in NFC form"))
    out.append(Mutation("encoding", name, value,
                        urllib.parse.quote(value, safe="") + "%20",
                        "fully percent-encoded with a trailing encoded space"))
    out.append(Mutation("encoding", name, value, value.upper(),
                        "case variation"))
    out.append(Mutation("encoding", name, value, value + "\u200b",
                        "zero-width space appended"))
    return out


def json_mutations(record):
    """JSON field mutations, including type changes and duplicate keys."""
    base = _clone(record)
    content_type = _content_type(base["headers"])
    if "json" not in content_type:
        return []
    try:
        data = json.loads(base["body"] or "null")
    except (json.JSONDecodeError, TypeError):
        return []
    out = []
    for path in _leaf_paths(data):
        original = _get_path(data, path)
        # Stored as JSON literals, not as rendered labels: `_literal()` reverses
        # exactly this encoding, so what the report says a mutation did and what
        # it sends are the same thing.
        replacements = (("null", "null"), ("empty string", '""'), ("boolean", "true"),
                        ("array", "[]"), ("object", "{}"))
        for label, literal in replacements:
            value = json.loads(literal)
            if type(original) is type(value):
                continue
            out.append(Mutation("json", path, _short(original), literal,
                                f"field type changed to {label}"))
        if isinstance(original, str):
            out.append(Mutation("json", path, _short(original),
                                json.dumps(original + original),
                                "string repeated"))
    return out


def _content_type(headers):
    for name, value in headers.items():
        if name.lower() == "content-type":
            return (value or "").lower()
    return ""


def _leaf_paths(node, path=""):
    """Paths to every leaf, so a mutation targets one value and nothing else."""
    out = []
    if isinstance(node, dict):
        for key in node:
            out.extend(_leaf_paths(node[key], f"{path}.{key}" if path else key))
    elif isinstance(node, list):
        for index, item in enumerate(node[:10]):
            out.extend(_leaf_paths(item, f"{path}[{index}]"))
    else:
        if path:
            out.append(path)
    return out


def _parse_path(path):
    """`a.b[0].c` -> ['a', 'b', 0, 'c']."""
    parts = []
    for chunk in path.split("."):
        while "[" in chunk:
            head, rest = chunk.split("[", 1)
            if head:
                parts.append(head)
                chunk = rest
            index, chunk = rest.split("]", 1)
            parts.append(int(index) if index.isdigit() else index)
            if chunk.startswith("."):
                chunk = chunk[1:]
        if chunk:
            parts.append(chunk)
    return parts


def _get_path(node, path):
    for key in _parse_path(path):
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            return None
    return node


def set_path(node, path, value):
    """Return a copy of `node` with one path replaced. Never mutates the input."""
    clone = json.loads(json.dumps(node))
    parts = _parse_path(path)
    cursor = clone
    for key in parts[:-1]:
        cursor = cursor[key]
    cursor[parts[-1]] = value
    return clone


def cookie_mutations(record):
    base = _clone(record)
    out = []
    for name, value in base["headers"].items():
        if name.lower() != "cookie":
            continue
        for pair in value.split(";"):
            if "=" not in pair:
                continue
            key, val = pair.split("=", 1)
            key, val = key.strip(), val.strip()
            out.append(Mutation("cookie", key, val, "", "cookie value emptied"))
            out.append(Mutation("cookie", key, val, val + "x",
                                "cookie value extended"))
    return out


def form_mutations(record):
    """Mutations of a urlencoded body, addressed by field name.

    The `form` kind had no builder: the catalogue mapped it to the query
    builder, so a form body was never mutated and the mutations that came back
    were labelled `query`. Applying them wrote a field into the URL of a request
    whose parameters are in the body.
    """
    base = _clone(record)
    if "form-urlencoded" not in _content_type(base["headers"]):
        return []
    pairs = urllib.parse.parse_qsl(base["body"] or "", keep_blank_values=True)
    out = []
    for name, value in pairs[:20]:
        out.append(Mutation("form", name, value, "", "field emptied"))
        out.append(Mutation("form", name, value, value + value, "field value repeated"))
    if pairs:
        name, value = pairs[0]
        out.append(Mutation("form", name, value, "second-value",
                            "the same field sent twice with different values",
                            mode="append"))
    else:
        out.append(Mutation("form", "field", None, "1", "an undocumented field",
                            mode="add"))
    return out


def content_type_mutations(record):
    base = _clone(record)
    declared = _content_type(base["headers"])
    if not declared:
        return []
    out = []
    if "json" in declared:
        out.append(Mutation("content-type", "Content-Type", declared,
                            "application/x-www-form-urlencoded",
                            "declared type changed to form encoding"))
    else:
        out.append(Mutation("content-type", "Content-Type", declared,
                            "application/json",
                            "declared type changed to JSON"))
    out.append(Mutation("content-type", "Content-Type", declared,
                        declared + "; charset=utf-16",
                        "an unexpected charset"))
    return out


def method_mutations(record):
    """Read-only method changes.

    A method change to a write verb is a different request to the target, not a
    variation of this one, so it is never generated here. `state_changing_methods`
    reports the verbs that would be interesting to test explicitly, and the
    operator sends them deliberately through the scope gate.
    """
    base = _clone(record)
    out = []
    for method in ("GET", "HEAD", "OPTIONS"):
        if method != base["method"]:
            out.append(Mutation("method", "method", base["method"], method,
                                "same request, different read-only verb"))
    return out


def catalogue(record, kinds=None):
    """Every mutation for a record, in a stable order."""
    builders = {
        "header": header_mutations,
        "query": query_mutations,
        "json": json_mutations,
        "form": form_mutations,
        "cookie": cookie_mutations,
        "method": method_mutations,
        "encoding": encoding_mutations,
        "content-type": content_type_mutations,
    }
    chosen = kinds or KINDS
    out = []
    for kind in chosen:
        builder = builders.get(kind)
        if builder:
            out.extend(builder(record))
    return _tidy(out)


def _tidy(mutations):
    """Drop no-ops and duplicates.

    A mutation whose value is unchanged is not a test: it is the original
    request sent again under a new label, and it spends a request from a
    deliberately finite budget while producing a result that looks like a
    negative. Duplicates arrive from different builders (a parameter whose
    duplicate-parameter case and whose encoding case resolve to the same request
    is one request, not two).
    """
    seen, out = set(), []
    for mutation in mutations:
        if str(mutation.before) == str(mutation.after) and mutation.before is not None:
            continue
        key = (mutation.kind, mutation.target, mutation.mode,
               str(mutation.before), str(mutation.after))
        if key in seen:
            continue
        seen.add(key)
        out.append(mutation)
    return out


def apply(record, mutation):
    """Produce the mutated request as a plain dict, without sending anything.

    Returns `(url, method, headers, body, conflict)` where `conflict` explains
    why a mutation could not be applied (a missing path, an unparsable body).
    """
    base = _clone(record)
    headers, body, method = dict(base["headers"]), base["body"], base["method"]
    url = base["url"]

    if mutation.kind == "header":
        if mutation.after is None:
            headers.pop(mutation.target, None)
        else:
            headers[mutation.target] = mutation.after
    elif mutation.kind in ("query", "encoding"):
        parsed = urllib.parse.urlsplit(url)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if mutation.mode in ("add", "append"):
            pairs.append((mutation.target, mutation.after))
        else:
            replaced = False
            for index, (name, value) in enumerate(pairs):
                if name == mutation.target and str(value) == str(mutation.before):
                    pairs[index] = (name, mutation.after)
                    replaced = True
                    break
            if not replaced:
                return url, method, headers, body, (
                    f"no parameter {mutation.target!r} with the expected value")
        url = _reencode(url, pairs)
    elif mutation.kind == "json":
        try:
            data = json.loads(body or "null")
        except (json.JSONDecodeError, TypeError) as exc:
            return url, method, headers, body, f"body is not JSON: {exc}"
        try:
            value = _literal(mutation.after)
            body = json.dumps(set_path(data, mutation.target, value))
        except (KeyError, IndexError, TypeError) as exc:
            return url, method, headers, body, f"path not present: {exc}"
    elif mutation.kind == "form":
        pairs = urllib.parse.parse_qsl(body or "", keep_blank_values=True)
        if mutation.mode in ("add", "append"):
            pairs.append((mutation.target, mutation.after))
        else:
            pairs = [(n, mutation.after if (n == mutation.target and str(v) == str(mutation.before))
                      else v) for n, v in pairs]
        body = urllib.parse.urlencode(pairs)
    elif mutation.kind == "cookie":
        new_cookies = []
        for pair in headers.get("Cookie", "").split(";"):
            if "=" not in pair:
                continue
            key, val = pair.split("=", 1)
            if key.strip() == mutation.target:
                new_cookies.append(f"{key.strip()}={mutation.after}")
            else:
                new_cookies.append(f"{key.strip()}={val.strip()}")
        headers["Cookie"] = "; ".join(new_cookies)
    elif mutation.kind == "method":
        method = mutation.after
    elif mutation.kind == "content-type":
        headers["Content-Type"] = mutation.after
    return url, method, headers, body, None


def _literal(text):
    """Turn a stored JSON-kind mutation value back into the value to apply.

    Values for the `json` kind are stored as JSON literals (`null`, `""`, `[]`),
    so this is a decode rather than a guess. Anything that is not valid JSON is
    passed through as the string it is, which is what the callers that build
    values by hand rely on.
    """
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def state_changing_methods(record):
    """Write verbs that are not already the request's method.

    Reported, never sent automatically. A deliberate authorization test changes
    whose request it is or what it does, and that is a decision for a human.
    """
    base = _clone(record)
    return [m for m in ("POST", "PUT", "PATCH", "DELETE") if m != base["method"]]


def describe_all(record, kinds=None):
    return [m.as_dict() for m in catalogue(record, kinds)]
