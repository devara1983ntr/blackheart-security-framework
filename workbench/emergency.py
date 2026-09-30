"""Emergency mode: a fast, read-only snapshot of what a target is serving.

What it is for
--------------
Something is wrong and somebody needs facts now: is the site up, what is it
saying, what certificate is it presenting, does it still point where it did, are
the baseline headers there. This collects that in a bounded number of read-only
requests and writes it as a verifiable bundle.

Read-only, and not by configuration
-----------------------------------
There is no option here that sends a write request: the method whitelist is a
module constant, every request goes through one private helper that asserts
against it, and a test scans the module's own AST to prove no call site could
pass anything else. An emergency is exactly when somebody would most like a tool
to "just try" something, so the tool has no capacity to.

What it is not
--------------
Not an assessment. It sends a handful of requests to one target, reads the
target's own published documents, and stops. It does not discover, fuzz, mutate
or compare identities, and the report says so in those words, because an
operator under pressure will read whatever the output says about itself.
"""

from __future__ import annotations

import urllib.parse

from . import checks
from . import evidence as ev
from . import fetch as fetchmod
from . import history as hist
from . import http_client as hc

# The complete set of methods this module can send. Not a default, not a
# parameter: the tuple is the whole surface.
READ_ONLY_METHODS = ("GET", "HEAD")

# Small on purpose. An emergency collection should finish, and a large body
# slows it without adding a fact the report needs.
BODY_CAP_BYTES = 64_000
METADATA_CAP_BYTES = 16_000

WELL_KNOWN_DOCUMENTS = ("/robots.txt", "/.well-known/security.txt")


class EmergencyError(Exception):
    """Raised when a collection cannot be attempted as asked."""


class EmergencyCollection:
    """What was observed, in the order it was observed."""

    def __init__(self, target, scope, budget):
        self.target = target
        self.scope = scope or {}
        self.budget = budget
        self.started_at = None
        self.finished_at = None
        self.facts = []
        self.documents = []
        self.evidence_ids = []
        self.errors = []
        self.refusals = []
        self.requests_used = 0
        self.cancelled = False

    def fact(self, name, value, source):
        self.facts.append({"fact": name, "value": value, "source": source,
                           "observed_at": fetchmod.now()})
        return self

    def get(self, name):
        for fact in self.facts:
            if fact["fact"] == name:
                return fact["value"]
        return None

    def summary(self):
        return {
            "mode": "emergency",
            "target": self.target,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "requests_used": self.requests_used,
            "budget": self.budget,
            "facts": len(self.facts),
            "documents": len(self.documents),
            "evidence_records": len(self.evidence_ids),
            "refusals": len(self.refusals),
            "errors": len(self.errors),
            "cancelled": self.cancelled,
            "read_only": True,
            "methods_sent": list(READ_ONLY_METHODS),
            "note": ("An emergency collection is a snapshot of what this target served "
                     "to a small number of read-only requests, taken once. It is not an "
                     "assessment, it is not a scan, and it does not establish that "
                     "anything is absent."),
        }

    def as_dict(self):
        return {
            "summary": self.summary(),
            "facts": self.facts,
            "documents": self.documents,
            "evidence_ids": self.evidence_ids,
            "refusals": self.refusals,
            "errors": self.errors,
        }

    def report_lines(self):
        summary = self.summary()
        lines = [
            "EMERGENCY COLLECTION (read-only, one pass)",
            f"  target          : {summary['target']}",
            f"  started         : {summary['started_at']}",
            f"  finished        : {summary['finished_at']}",
            f"  requests        : {summary['requests_used']} of {summary['budget']}",
        ]
        if summary["cancelled"]:
            lines.append("  cancelled       : yes — partial results retained")
        lines.append("")
        for fact in self.facts:
            lines.append(f"  {fact['fact']:28} {fact['value']}")
        if self.documents:
            lines.append("")
            lines.append("  published documents read")
            for document in self.documents:
                lines.append(f"    {document['url']}: {document['status']}")
        if self.refusals:
            lines.append("")
            lines.append("  refused by the scope file")
            for refusal in self.refusals:
                lines.append(f"    {refusal['url']}: {refusal['reason']}")
        lines.append("")
        lines.append("  This is a snapshot, not an assessment. It does not discover, "
                     "fuzz or compare identities, and an empty section means the "
                     "collection did not cover it — not that nothing is there.")
        return "\n".join(lines)


def _read_only_request(guard, url, method, collection, *, history=None, max_bytes=None,
                       note=""):
    """The only way this module sends a request, so the whitelist cannot be missed."""
    if method not in READ_ONLY_METHODS:
        raise EmergencyError(
            f"emergency mode is read-only: it sends {', '.join(READ_ONLY_METHODS)} "
            f"only, and {method} was requested")
    try:
        exchange = hc.request(guard, url, method, max_bytes=max_bytes,
                              note=f"emergency:{note or method.lower()}")
    except Exception as exc:                                  # ScopeError included
        collection.refusals.append({"url": url, "reason": f"{type(exc).__name__}: {exc}"})
        return None
    collection.requests_used += 1
    if history is not None:
        history.add(exchange, tag="emergency")
    return exchange.record()


def collect(guard, target_url, *, history=None, bundle=None, budget=None,
            cancel_check=None, include_documents=True, tag="emergency"):
    """Collect a read-only snapshot of one authorised target.

    `budget` bounds the requests this run makes. `bundle`, when given, receives
    the evidence records the standard checks produce from the responses — the
    same checks the normal path uses, so an emergency record and a routine
    record look the same to whoever reads them later.
    """
    scope = guard.scope
    budget = int(budget if budget is not None else min(scope.max_requests, 20))
    collection = EmergencyCollection(target_url, guard.summary(), budget)
    collection.started_at = fetchmod.now()
    history = history or hist.History()

    def stop():
        if collection.requests_used >= budget:
            collection.errors.append("stopped at the request budget")
            return True
        return bool(cancel_check is not None and cancel_check())

    try:
        record = _read_only_request(guard, target_url, "HEAD", collection,
                                    history=history, max_bytes=METADATA_CAP_BYTES,
                                    note="head")
        if record is None or not (record.get("response") or {}).get("status"):
            record = _read_only_request(guard, target_url, "GET", collection,
                                        history=history, max_bytes=BODY_CAP_BYTES,
                                        note="get")
        if record is None:
            collection.errors.append("the target could not be reached")
            return collection
        _record_response_facts(collection, record, target_url)
        if not (record.get("response") or {}).get("status"):
            # A transport failure leaves a record with the error in it and no
            # status. Recording the facts and the reason beats returning an
            # empty collection that looks like a target with nothing to say.
            collection.errors.append(
                "the target could not be reached: "
                + str((record.get("response") or {}).get("error") or "no response"))
            return collection

        # A HEAD carries no body, and "is it still serving the page it was" is one
        # of the questions people ask in an emergency. One bounded GET answers it
        # by hashing the first bytes that arrive; the body itself is not kept.
        if not stop():
            body_record = _read_only_request(guard, target_url, "GET", collection,
                                             history=history, max_bytes=BODY_CAP_BYTES,
                                             note="body-prefix")
            if body_record is not None:
                _record_body_facts(collection, body_record)

        if include_documents and not stop():
            for path in WELL_KNOWN_DOCUMENTS:
                if stop():
                    break
                url = _origin(target_url) + path
                document = _read_only_request(guard, url, "GET", collection,
                                              history=history,
                                              max_bytes=METADATA_CAP_BYTES,
                                              note=path.strip("/").replace("/", "-"))
                response = (document or {}).get("response") or {}
                collection.documents.append({
                    "url": url,
                    "status": response.get("status"),
                    "content_type": response.get("content_type"),
                    "bytes": response.get("bytes"),
                    "available": response.get("status") == 200,
                })
                if response.get("status") == 200 and document.get("response", {}).get(
                        "body_text"):
                    collection.fact(f"document {path}", "served", url)

        # The same checks the routine path runs, so an emergency bundle is not a
        # different kind of evidence.
        records = list(history.entries)
        produced = checks.run_checks(records, bundle=bundle,
                                     scope_summary=guard.summary())
        collection.evidence_ids = [item.id for item in produced]
    finally:
        collection.finished_at = fetchmod.now()
        if bundle is not None:
            bundle.notes = list(getattr(bundle, "notes", [])) + [
                "collected in emergency mode: read-only, one pass"]
    return collection


def _record_body_facts(collection, record):
    response = record.get("response") or {}
    body = response.get("body_text") or ""
    collection.fact("body bytes", response.get("bytes"), "the response body")
    if body:
        collection.fact("body prefix sha256", ev.sha256_text(body)[:32], "the response body")
    if response.get("truncated"):
        collection.fact("body truncated", "yes", "the client")
    for name, value in (response.get("headers") or {}).items():
        if name.lower() == "etag":
            collection.fact("header etag", value, "the response")
        elif name.lower() == "last-modified":
            collection.fact("header last-modified", value, "the response")
    return collection


def _origin(url):
    parsed = urllib.parse.urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _record_response_facts(collection, record, requested_url):
    """What one response says about the target, written down one fact at a time."""
    response = record.get("response") or {}
    collection.fact("requested url", requested_url, "the request")
    collection.fact("final url", record.get("final_url") or record.get("url"),
                    "the response")
    collection.fact("status", response.get("status"), "the response")
    if response.get("reason"):
        collection.fact("reason", response.get("reason"), "the response")
    collection.fact("content type", response.get("content_type"), "the response")
    if response.get("elapsed_ms") is not None:
        collection.fact("elapsed ms", response.get("elapsed_ms"), "the response")
    if response.get("error"):
        collection.fact("transport error", response.get("error"), "the client")
    if response.get("truncated"):
        collection.fact("body truncated", "yes", "the client")
    headers = response.get("headers") or {}
    for name in ("server", "date", "cache-control", "content-security-policy",
                 "strict-transport-security", "x-frame-options",
                 "x-content-type-options", "referrer-policy", "location"):
        for header, value in headers.items():
            if header.lower() == name:
                collection.fact(f"header {name}", value, "the response")
    tls = response.get("tls") or {}
    if tls:
        collection.fact("tls version", tls.get("version"), "the handshake")
        collection.fact("tls cipher", tls.get("cipher"), "the handshake")
        certificate = tls.get("cert") or {}
        if certificate.get("subject"):
            collection.fact("certificate subject", certificate.get("subject"),
                            "the handshake")
        if certificate.get("notAfter"):
            collection.fact("certificate expires", certificate.get("notAfter"),
                            "the handshake")
        if certificate.get("issuer"):
            collection.fact("certificate issuer", certificate.get("issuer"),
                            "the handshake")
    chain = record.get("redirect_chain") or []
    if chain:
        collection.fact("redirects", len(chain), "the response")
        for hop in chain:
            collection.fact(f"redirect {hop.get('status')}", hop.get("location"),
                            hop.get("from") or "the request")
    scope_decision = record.get("scope_decision") or {}
    if scope_decision:
        collection.fact("scope decision", scope_decision.get("rule"), "the scope gate")
    return collection


def plan_lines(guard, target_url, budget=None):
    """What an emergency collection will do, before it does any of it."""
    scope = guard.scope
    budget = int(budget if budget is not None else min(scope.max_requests, 20))
    return "\n".join([
        f"Emergency collection plan for {target_url}",
        f"  methods   : {', '.join(READ_ONLY_METHODS)} only",
        f"  requests  : at most {budget}",
        f"  reads     : the target URL, {', '.join(WELL_KNOWN_DOCUMENTS)}",
        f"  evidence  : written as records in the standard format",
        "  and nothing else: no discovery, no mutations, no writes",
    ])
