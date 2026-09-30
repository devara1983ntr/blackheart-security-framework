"""HTTP history: capture, storage, replay and comparison.

What this is
------------
The record of what was actually sent and what actually came back. Every other
analysis module reads from here rather than holding its own copy of a response,
so "the evidence" is one thing with one shape, and a report cannot quote a
response that was never received.

Two rules shape the storage format:

* **Redaction happens before persistence, not on the way out.** The in-memory
  exchange may hold the `Authorization` header it was given, because a replay
  needs it; the file on disk never does. Evidence directories get copied,
  attached to tickets and pasted into reports, and a redaction step that lives
  at the edge is a redaction step somebody will forget.
* **Replay is a new exchange, never an edit of the old one.** The original is
  the evidence for whatever claim is being made about the target, so replaying
  it with a changed header writes a new record that points at its parent. The
  history therefore shows what was tried in order, which is what makes a
  negative result meaningful.

`replay()` refuses state-changing methods unless the caller passes
`confirm_write=True` *and* the scope authorises the method. There is no
"replay all" that quietly includes a DELETE.
"""

from __future__ import annotations

import json
import os

from . import http_client as hc
from . import scope as sc

STORE_VERSION = 1


class History:
    """An ordered collection of exchanges for one engagement."""

    def __init__(self, path=None, secrets=()):
        self.entries = []
        self.path = path
        self.secrets = tuple(secrets)
        self._next_id = 1

    # -- capture ---------------------------------------------------------
    def add(self, exchange, tag="", parent=None):
        """Record an exchange and return its id. The only write path."""
        entry_id = f"H{self._next_id:04d}"
        self._next_id += 1
        record = exchange.record(secrets=self.secrets)
        record["id"] = entry_id
        record["tag"] = tag
        record["parent"] = parent
        self.entries.append(record)
        if self.path:
            self._append(record)
        return entry_id

    def _append(self, record):
        directory = os.path.dirname(os.path.abspath(self.path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    # -- read ------------------------------------------------------------
    def get(self, entry_id):
        for entry in self.entries:
            if entry["id"] == entry_id:
                return entry
        return None

    def last(self):
        return self.entries[-1] if self.entries else None

    def by_host(self, host):
        return [e for e in self.entries if (e.get("host") or "") == host]

    def to_dicts(self):
        return list(self.entries)

    def summary(self):
        """Counts by status class and method, for a report header."""
        by_method, by_status = {}, {}
        for entry in self.entries:
            by_method[entry["method"]] = by_method.get(entry["method"], 0) + 1
            response = entry.get("response") or {}
            status = response.get("status")
            key = f"{status // 100}xx" if isinstance(status, int) else "no-response"
            by_status[key] = by_status.get(key, 0) + 1
        return {"entries": len(self.entries), "by_method": by_method,
                "by_status": by_status}

    @classmethod
    def load(cls, path, secrets=()):
        """Read a history file written by `add`. Unparseable lines are reported."""
        hist = cls(path=None, secrets=secrets)
        skipped = []
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    skipped.append(lineno)
                    continue
                hist.entries.append(record)
                entry_id = record.get("id", "")
                if entry_id.startswith("H") and entry_id[1:].isdigit():
                    hist._next_id = max(hist._next_id, int(entry_id[1:]) + 1)
                else:
                    hist._next_id += 1
        hist.skipped_lines = skipped
        return hist


def capture(guard, url, method="GET", history=None, tag="", **kwargs):
    """Send a request through the guard and record it. The normal entry point."""
    exchange = hc.request(guard, url, method, **kwargs)
    if history is not None:
        return history.add(exchange, tag=tag), exchange
    return None, exchange


def replay(guard, exchange, *, headers=None, body=None, method=None,
           history=None, confirm_write=False, tag="replay", **kwargs):
    """Send a modified copy of a captured request, as a new record.

    The original is never mutated: the returned exchange has no parent link,
    but the record written to history carries the id of the request it came
    from, so a report can show the pair.
    """
    method = (method or exchange.method).upper()
    merged = dict(exchange.request_headers)
    if headers:
        merged.update(headers)
    payload = exchange.request_body if body is None else body
    new = hc.request(guard, exchange.url, method, headers=merged, body=payload,
                     confirm_write=confirm_write, **kwargs)
    if history is not None:
        entry_id = history.add(new, tag=tag)
        for entry in history.entries:
            if entry["id"] == entry_id:
                entry["replayed_from"] = exchange.url
                entry["original_request_headers"] = hc.redact_headers(
                    exchange.request_headers)
                entry["original_request_body"] = exchange.request_body.decode(
                    "utf-8", errors="replace")[:4096]
        return entry_id, new
    return None, new


def replay_from_record(guard, history, entry_id, *, headers=None, body=None,
                       method=None, confirm_write=False, tag="replay", **kwargs):
    """Replay a stored entry, which is the case a CLI has: a file, not an object."""
    entry = history.get(entry_id)
    if entry is None:
        raise KeyError(f"no history entry {entry_id}")
    if hc.url_is_redacted(entry.get("url")):
        raise ValueError(
            f"{entry_id} was recorded with a value redacted from its URL, so replaying "
            f"it would send the marker '[redacted]' where a credential was. Re-issue "
            f"the request with the value supplied again instead of replaying this one")
    stored_headers = dict(entry.get("request_headers") or {})
    if stored_headers:
        # Persisted headers are redacted, so a replay of a stored request cannot
        # silently reuse a credential — it must be supplied again. Replaying a
        # redacted header would send the literal string "[redacted]" and produce
        # a confusing 401 that looks like a finding.
        for name in list(stored_headers):
            if hc.is_redacted(stored_headers[name]):
                del stored_headers[name]
    if headers:
        stored_headers.update(headers)
    exchange = _ExchangeShell(entry)
    # The shell is built from the stored record, so it carries the same redacted
    # header the dict above just had removed. Clearing it on both is what makes
    # "the marker is never transmitted" true rather than aspirational.
    for name in list(exchange.request_headers):
        if hc.is_redacted(exchange.request_headers[name]):
            del exchange.request_headers[name]
    return replay(guard, exchange, headers=stored_headers, body=body,
                  method=method, history=history, confirm_write=confirm_write,
                  tag=tag, **kwargs)


class _ExchangeShell:
    """The minimum an exchange needs to look like one to `replay`."""

    def __init__(self, entry):
        self.url = entry["url"]
        self.method = entry["method"]
        self.request_headers = dict(entry.get("request_headers") or {})
        self.request_body = (entry.get("request_body") or "").encode()


def diff_against_previous(history, entry_id):
    """Compare an entry with the most recent earlier request to the same URL.

    Ordering matters, so this looks backwards from the entry rather than
    matching any pair with the same path.
    """
    from .diff import compare_records
    index = next((i for i, e in enumerate(history.entries) if e["id"] == entry_id), None)
    if index is None or index == 0:
        return None
    target = history.entries[index]
    for earlier in reversed(history.entries[:index]):
        if earlier["url"] == target["url"] and earlier["method"] == target["method"]:
            return compare_records(earlier, target)
    return None


def guard_shape(guard):
    """The scope summary, for embedding in a history file header."""
    return {"scope": sc.ScopeGuard.summary(guard)} if guard else None
