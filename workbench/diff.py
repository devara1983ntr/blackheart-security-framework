"""Deterministic comparison of two responses.

The vocabulary matters more than the algorithm here.

A difference between two responses is **an observable response difference** and
nothing more. It is not a finding, not a vulnerability, and not evidence of
access-control failure: an endpoint may legitimately answer differently for a
valid and an invalid input, a cache may serve an older body, and a load balancer
may return two different backends. The workbench therefore never writes the word
"vulnerable" next to a diff. What it writes is what changed, and the operator
decides what to test next.

The comparison is deterministic on purpose — same two inputs, same output, every
time — because a diff an operator cannot reproduce is not evidence. Nothing here
uses a threshold, a heuristic score or a fuzzy match: two bodies are equal or
they are not, JSON is compared structurally by key path, and HTML is compared
after a conservative normalisation that is documented at the function that does
it.
"""

from __future__ import annotations

import json
import re

# Language that must not appear in a diff result. Kept as data so the check can
# be applied to the serialised output rather than trusted to reviewers.
FORBIDDEN_CLAIMS = ("vulnerable", "vulnerability", "exploitable", "confirmed",
                    "attack successful", "bypass succeeded", "proof of")

MAX_BODY_COMPARE = 400_000


def _status_class(status):
    return None if not isinstance(status, int) else status // 100


def compare_headers(a, b):
    """Header-by-header difference: added, removed, changed.

    Header *values* are compared, but only for names present on either side, and
    the result keeps both values so a reviewer sees what changed rather than
    that something changed.
    """
    a = {k.lower(): v for k, v in (a or {}).items()}
    b = {k.lower(): v for k, v in (b or {}).items()}
    added = {k: b[k] for k in sorted(b) if k not in a}
    removed = {k: a[k] for k in sorted(a) if k not in b}
    changed = {k: {"from": a[k], "to": b[k]}
               for k in sorted(set(a) & set(b)) if a[k] != b[k]}
    return {"added": added, "removed": removed, "changed": changed,
            "count": len(added) + len(removed) + len(changed)}


def parse_cookies(set_cookie_values):
    """Parse `Set-Cookie` into name → attributes, without a cookie library.

    Only the shape needed for comparison and for the cookie-flag check: the
    value is kept (it is the target's, not the operator's) and the flags are
    recorded.
    """
    cookies = {}
    for raw in set_cookie_values if isinstance(set_cookie_values, list) else [set_cookie_values]:
        if not raw:
            continue
        parts = [p.strip() for p in str(raw).split(";")]
        if not parts or "=" not in parts[0]:
            continue
        name, value = parts[0].split("=", 1)
        attrs = {}
        for attr in parts[1:]:
            if not attr:
                continue
            if "=" in attr:
                k, v = attr.split("=", 1)
                attrs[k.strip().lower()] = v.strip()
            else:
                attrs[attr.strip().lower()] = True
        cookies[name.strip()] = {"value": value.strip(), "attributes": attrs}
    return cookies


def cookies_from_record(record):
    """Every `Set-Cookie` on a stored response, parsed. Handles a folded list."""
    response = (record or {}).get("response") or {}
    headers = response.get("headers") or {}
    raw = [v for k, v in headers.items() if k.lower() == "set-cookie"]
    return parse_cookies(raw)


def compare_cookies(a, b):
    a_c, b_c = cookies_from_record(a), cookies_from_record(b)
    added = {k: v for k, v in b_c.items() if k not in a_c}
    removed = {k: v for k, v in a_c.items() if k not in b_c}
    changed = {}
    for name in sorted(set(a_c) & set(b_c)):
        before, after = a_c[name], b_c[name]
        if before == after:
            continue
        entry = {}
        if before["value"] != after["value"]:
            entry["value"] = "changed"
        flag_diff = {k: {"from": before["attributes"].get(k),
                         "to": after["attributes"].get(k)}
                     for k in set(before["attributes"]) | set(after["attributes"])
                     if before["attributes"].get(k) != after["attributes"].get(k)}
        if flag_diff:
            entry["attributes"] = flag_diff
        changed[name] = entry
    return {"added": added, "removed": removed, "changed": changed,
            "count": len(added) + len(removed) + len(changed)}


def normalise_text(text):
    """Conservative normalisation for the *normalised* body comparison.

    Deliberately narrow: trailing whitespace per line, line-ending style, and
    runs of spaces inside a line. Anything more (case folding, markup stripping,
    numeric masking) starts hiding real differences, and a comparison that
    hides differences is worse than one that reports a few irrelevant ones.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")).strip()


def body_diff(a_text, b_text):
    """Exact and normalised equality, plus a first-divergence pointer."""
    a_text = a_text or ""
    b_text = b_text or ""
    exact = a_text == b_text
    normalised = normalise_text(a_text) == normalise_text(b_text)
    result = {
        "exact_equal": exact,
        "normalised_equal": normalised,
        "length_from": len(a_text),
        "length_to": len(b_text),
    }
    if not normalised:
        result["first_difference"] = _first_difference(a_text, b_text)
    return result


def _first_difference(a, b, window=60):
    limit = min(len(a), len(b))
    at = next((i for i in range(limit) if a[i] != b[i]), limit)
    start = max(0, at - 20)
    return {
        "offset": at,
        "from": a[start:at + window],
        "to": b[start:at + window],
    }


def json_structure(value, path="$", depth=0, max_depth=12):
    """Flatten JSON to `path: type` pairs.

    Structural comparison is about keys and types, not values: an endpoint that
    stops returning a field has changed shape, and an endpoint that changes a
    value has not. Depth is capped so a pathological document cannot produce an
    unbounded walk.
    """
    pairs = {}
    if depth > max_depth:
        pairs[path] = "truncated"
        return pairs
    if isinstance(value, dict):
        pairs[path] = "object"
        for key in sorted(value):
            pairs.update(json_structure(value[key], f"{path}.{key}", depth + 1, max_depth))
    elif isinstance(value, list):
        pairs[path] = f"array[{len(value)}]"
        for i, item in enumerate(value[:50]):
            pairs.update(json_structure(item, f"{path}[{i}]", depth + 1, max_depth))
    elif isinstance(value, bool):
        pairs[path] = "boolean"
    elif isinstance(value, (int, float)):
        pairs[path] = "number"
    elif value is None:
        pairs[path] = "null"
    else:
        pairs[path] = "string"
    return pairs


def compare_json(a_text, b_text):
    """Structural JSON comparison; returns `parsed: False` when either side is not JSON."""
    try:
        a = json.loads(a_text or "null")
    except (json.JSONDecodeError, TypeError):
        return {"parsed": False, "reason": "first response is not JSON"}
    try:
        b = json.loads(b_text or "null")
    except (json.JSONDecodeError, TypeError):
        return {"parsed": False, "reason": "second response is not JSON"}
    a_shape, b_shape = json_structure(a), json_structure(b)
    added = {k: b_shape[k] for k in sorted(set(b_shape) - set(a_shape))}
    removed = {k: a_shape[k] for k in sorted(set(a_shape) - set(b_shape))}
    retyped = {k: {"from": a_shape[k], "to": b_shape[k]}
               for k in sorted(set(a_shape) & set(b_shape)) if a_shape[k] != b_shape[k]}
    return {"parsed": True, "added_keys": added, "removed_keys": removed,
            "changed_types": retyped,
            "count": len(added) + len(removed) + len(retyped)}


def _record_parts(record):
    response = (record or {}).get("response") or {}
    return {
        "status": response.get("status"),
        "headers": response.get("headers") or {},
        "body_text": response.get("body_text") or "",
        "content_type": response.get("content_type") or "",
        "bytes": response.get("bytes"),
        "elapsed_ms": response.get("elapsed_ms"),
    }


def compare_records(a, b):
    """Compare two stored records. The single entry point for comparison."""
    ra, rb = _record_parts(a), _record_parts(b)
    status = {
        "from": ra["status"], "to": rb["status"],
        "changed": ra["status"] != rb["status"],
        "class_changed": _status_class(ra["status"]) != _status_class(rb["status"]),
    }
    headers = compare_headers(ra["headers"], rb["headers"])
    cookies = compare_cookies(a, b)
    body = body_diff(ra["body_text"][:MAX_BODY_COMPARE], rb["body_text"][:MAX_BODY_COMPARE])
    structural = compare_json(ra["body_text"], rb["body_text"])
    timing = {"from_ms": ra["elapsed_ms"], "to_ms": rb["elapsed_ms"],
              "delta_ms": (rb["elapsed_ms"] - ra["elapsed_ms"])
              if isinstance(ra["elapsed_ms"], int) and isinstance(rb["elapsed_ms"], int)
              else None}
    differences = [status["changed"], headers["count"] > 0, cookies["count"] > 0,
                   not body["normalised_equal"],
                   bool(structural.get("parsed") and structural.get("count")),
                   timing["delta_ms"] not in (None, 0)]
    return {
        "observable_response_difference": True,
        "from": {"id": a.get("id"), "url": a.get("url"), "method": a.get("method")},
        "to": {"id": b.get("id"), "url": b.get("url"), "method": b.get("method")},
        "status": status,
        "headers": headers,
        "cookies": cookies,
        "body": body,
        "json_structure": structural,
        "content_type": {"from": ra["content_type"], "to": rb["content_type"],
                         "changed": ra["content_type"] != rb["content_type"]},
        "byte_length": {"from": ra["bytes"], "to": rb["bytes"]},
        "timing": timing,
        "difference_count": sum(1 for d in differences if d),
        "interpretation": ("An observable response difference. This is not by itself "
                           "evidence of a defect: it states that two responses differ "
                           "and how. Validation is a separate step, recorded separately."),
    }


def compare_exchanges(a_exchange, b_exchange, id_a=None, id_b=None):
    """Compare two live exchanges by serialising them through the same shape."""
    a = a_exchange.record()
    b = b_exchange.record()
    a["id"], b["id"] = id_a, id_b
    return compare_records(a, b)


def as_text(result):
    """A readable rendering, used by the CLI."""
    lines = [f"Observable response difference: {result['difference_count']} section(s) changed"]
    status = result["status"]
    if status["changed"]:
        lines.append(f"  status      : {status['from']} -> {status['to']}")
    for section in ("headers", "cookies"):
        block = result[section]
        if block["count"]:
            lines.append(f"  {section:11} : +{len(block['added'])} "
                         f"-{len(block['removed'])} ~{len(block['changed'])}")
            for name in sorted(block["added"])[:8]:
                lines.append(f"      + {name}")
            for name in sorted(block["removed"])[:8]:
                lines.append(f"      - {name}")
            for name in sorted(block["changed"])[:8]:
                lines.append(f"      ~ {name}")
    body = result["body"]
    if not body["normalised_equal"]:
        lines.append(f"  body        : {body['length_from']} -> {body['length_to']} bytes")
        first = body.get("first_difference", {})
        if first:
            lines.append(f"      first difference at offset {first['offset']}")
    structural = result["json_structure"]
    if structural.get("parsed") and structural.get("count"):
        lines.append(f"  json        : +{len(structural['added_keys'])} "
                     f"-{len(structural['removed_keys'])} "
                     f"~{len(structural['changed_types'])}")
    if result["content_type"]["changed"]:
        lines.append(f"  content-type: {result['content_type']['from']} -> "
                     f"{result['content_type']['to']}")
    timing = result["timing"]
    if timing["delta_ms"] is not None:
        lines.append(f"  timing      : {timing['from_ms']}ms -> {timing['to_ms']}ms")
    lines.append("")
    lines.append("  A difference is not a finding. Nothing here is validated.")
    return "\n".join(lines)


def assert_no_overclaim(rendered):
    """Guard used by the tests and the reporting layer.

    The rule that a diff must not claim a defect is enforced by inspecting the
    output rather than by remembering to phrase things carefully.
    """
    lowered = rendered.lower()
    return [word for word in FORBIDDEN_CLAIMS if word in lowered]
