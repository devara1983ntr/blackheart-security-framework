"""A bounded fuzzing engine.

Design position
---------------
A fuzzer is the most dangerous thing in this workbench, because it sends many
requests and it sends them without a human reading each one. Everything that
makes it safe is therefore a limit, and every limit is enforced here rather than
by the caller:

* **Request budget** — from the scope file, counted across the whole run.
* **Concurrency** — from the scope file, and never more workers than jobs.
* **Rate limit** — from the scope file, applied by the guard between requests.
* **Timeout** — per request, from the scope file, so one slow endpoint cannot
  hold the run open.
* **Cancellation** — a check between requests, so a run stops at a boundary
  rather than mid-flight, and partial results survive.
* **Target allowlist** — every request goes through `ScopeGuard`, with no
  exception for "internal" calls.
* **Destructive-method protection** — mutations of a write request are refused
  unless the caller explicitly allows state-changing traffic, and a mutation
  that would change a read request into a write request is never generated.
* **Audit log** — every attempt, its mutation, its scope decision and its
  outcome, in order.

What it is not
--------------
Not a WAF-evasion engine, not a payload injector, not a brute-forcer. The
mutation catalogue is structural (see `mutate.py`), the engine refuses to send
the same request twice, and the results are described as observable differences
until a human validates them. A fuzzing run that finds nothing is a normal
outcome and is reported as coverage, not as a clean bill of health.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import diff as diffmod
from . import http_client as hc
from . import mutate as mutatemod
from . import scope as sc

# Mutation kinds that change what the target does rather than how it reads what
# it was given. Method changes to write verbs are never generated at all; a write
# mutation on a write request is what these kinds are about.
STATE_CHANGING_KINDS = ("method",)


class Cancelled(Exception):
    """Raised inside a run when cancellation is requested between requests."""


class FuzzResult:
    """One mutation, its outcome, and the comparison against the base response."""

    def __init__(self, index, mutation, decision, record=None, error=None,
                 duplicate_of=None):
        self.index = index
        self.mutation = mutation
        self.decision = decision
        self.record = record
        self.error = error
        self.duplicate_of = duplicate_of
        self.difference = None

    @property
    def status(self):
        if self.error:
            return "error"
        if not self.decision.get("allowed"):
            return "blocked"
        response = (self.record or {}).get("response") or {}
        return response.get("status")

    def as_dict(self, include_body=False):
        payload = {
            "index": self.index,
            "mutation": self.mutation.as_dict(),
            "scope_decision": self.decision,
            "status": self.status,
            "duplicate_of": self.duplicate_of,
            "error": self.error,
        }
        if self.record:
            response = self.record.get("response") or {}
            payload["response"] = {
                "status": response.get("status"),
                "bytes": response.get("bytes"),
                "content_type": response.get("content_type"),
                "elapsed_ms": response.get("elapsed_ms"),
                "error": response.get("error"),
                "truncated": response.get("truncated"),
            }
            if include_body:
                payload["response"]["body_text"] = response.get("body_text")
        if self.difference:
            payload["difference_count"] = self.difference["difference_count"]
            payload["status_changed"] = self.difference["status"]["changed"]
            payload["interpretation"] = self.difference["interpretation"]
        return payload


class FuzzRun:
    """The result of one run, plus the accounting a report needs."""

    def __init__(self, base, budget, plan):
        self.base = base
        self.budget = budget
        self.plan = plan
        self.results = []
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.finished_at = None
        self.cancelled = False
        self.requests_sent = 0
        self.duplicates_skipped = 0
        self.plan_truncated = 0
        self.plan_source = "catalogue"

    def summary(self):
        interesting = [r for r in self.results if r.difference
                       and r.difference["difference_count"] > 0]
        statuses = {}
        for result in self.results:
            key = str(result.status)
            statuses[key] = statuses.get(key, 0) + 1
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "planned": self.plan,
            "plan_source": self.plan_source,
            "plan_truncated_by_budget": self.plan_truncated,
            "executed": len(self.results),
            "requests_sent": self.requests_sent,
            "budget": self.budget,
            "cancelled": self.cancelled,
            "duplicates_skipped": self.duplicates_skipped,
            "differences_observed": len(interesting),
            "by_status": statuses,
            "note": ("Differences are observable response differences, not findings. "
                     "Validation is a separate, human step."),
        }


def plan_mutations(record, kinds=None, limit=None):
    """The mutation list for a record, optionally capped at `limit`."""
    mutations = mutatemod.catalogue(record, kinds)
    if limit is not None:
        mutations = mutations[:limit]
    return mutations


def _cache_key(url, method, headers, body):
    """Identity of a request for de-duplication, ignoring header order."""
    header_key = ";".join(f"{k.lower()}={v}" for k, v in sorted(headers.items()))
    return f"{method} {url} {header_key} {body}"


def run(guard, base_record, *, kinds=None, budget=None, limit=None, plan=None,
        history=None, tag="fuzz", cancel_check=None, allow_state_changing=False,
        compare=True):
    """Execute a bounded fuzzing run against one captured request.

    `base_record` is a stored record (the shape `history` holds), never a live
    exchange: a run starts from something that was already captured, which is
    what keeps "what was sent" auditable.

    `plan` lets a caller send a mutation list that was reviewed before the run —
    which is how a deliberate write-method test is expressed, and how a CLI can
    show an operator what is about to be sent. Every safety rule below still
    applies to a supplied plan: it is a list of intentions, not a bypass.
    """
    scope_obj = guard.scope
    if hc.url_is_redacted(base_record.get("url")):
        # The base record's URL is what every mutation is built from. If it
        # carries a redaction marker, the whole run would send that marker, and
        # the results would be differences against a request nobody made.
        raise ValueError(
            "the base record's URL has a redacted value in it, so every mutation "
            "would send the marker '[redacted]' instead of the credential. Capture "
            "the request again with the value supplied, then fuzz from that record")
    budget = int(budget if budget is not None else scope_obj.max_requests)
    remaining_budget = max(0, budget - guard.requests_made)
    if plan is not None:
        full_plan = list(plan)
    else:
        full_plan = plan_mutations(base_record, kinds)
    mutations = list(full_plan)
    if limit is not None:
        mutations = mutations[:limit]
    if len(mutations) > remaining_budget:
        mutations = mutations[:remaining_budget]

    base_exchange = hc.Exchange(base_record.get("url", ""), base_record.get("method", "GET"),
                                {}, b"", note="fuzz base")
    base_exchange.response = _response_from_record(base_record)
    base_serialised = base_record

    run_state = FuzzRun(base_record, budget, len(mutations))
    run_state.plan_truncated = len(full_plan) - len(mutations)
    run_state.plan_source = "explicit" if plan is not None else "catalogue"
    stop_event = threading.Event()
    seen = {_cache_key(base_record.get("url", ""), base_record.get("method", "GET"),
                       base_record.get("request_headers") or {},
                       base_record.get("request_body") or "")}
    lock = threading.Lock()

    def execute(index, mutation):
        # Cancellation is checked here, at the top of every job, so a worker that
        # has not started yet stops before it opens a connection. A run that
        # "cancels" but keeps sending is worse than one that ignores the signal,
        # because the operator believes it stopped.
        if stop_event.is_set() or (cancel_check is not None and cancel_check()):
            raise Cancelled()
        if guard.requests_made >= scope_obj.max_requests:
            return FuzzResult(index, mutation,
                              {"allowed": False, "rule": "budget",
                               "reason": "request budget exhausted"},
                              error="budget exhausted")
        url, method, headers, body, conflict = mutatemod.apply(base_record, mutation)
        if conflict:
            return FuzzResult(index, mutation,
                              {"allowed": False, "rule": "mutation", "reason": conflict},
                              error=conflict)
        if (method in sc.WRITE_METHODS and method != base_record.get("method")
                and not allow_state_changing):
            return FuzzResult(index, mutation,
                              {"allowed": False, "rule": "destructive",
                               "reason": f"{method} changes state on the target"},
                              error="state-changing request refused")
        key = _cache_key(url, method, headers, body)
        with lock:
            if key in seen:
                run_state.duplicates_skipped += 1
                return FuzzResult(index, mutation,
                                  {"allowed": True, "rule": "duplicate",
                                   "reason": "identical to an earlier request"},
                                  duplicate_of="earlier request")
            seen.add(key)

        decision = guard.check(url, method)
        if not decision:
            return FuzzResult(index, mutation, decision.as_dict())
        exchange = hc.request(guard, url, method, headers=headers,
                              body=body.encode() if isinstance(body, str) else body,
                              confirm_write=allow_state_changing)
        with lock:
            run_state.requests_sent += 1
        record = exchange.record()
        record["id"] = f"F{index:03d}"
        if history is not None:
            history.add(exchange, tag=tag)
        result = FuzzResult(index, mutation, decision.as_dict(), record=record)
        if compare:
            result.difference = diffmod.compare_records(base_serialised, record)
        return result

    workers = max(1, min(int(scope_obj.max_concurrency), max(1, len(mutations))))
    try:
        if workers == 1:
            for index, mutation in enumerate(mutations, 1):
                run_state.results.append(execute(index, mutation))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(execute, index, mutation)
                           for index, mutation in enumerate(mutations, 1)]
                for future in futures:
                    try:
                        run_state.results.append(future.result())
                    except Cancelled:
                        run_state.cancelled = True
                        stop_event.set()
                        break
    except Cancelled:
        run_state.cancelled = True
        stop_event.set()
    finally:
        run_state.results.sort(key=lambda r: r.index)
        run_state.finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return run_state


def _response_from_record(record):
    response = hc.Response()
    stored = (record or {}).get("response") or {}
    response.status = stored.get("status")
    response.headers = dict(stored.get("headers") or {})
    response.body = (stored.get("body_text") or "").encode("utf-8", errors="replace")
    response.elapsed_ms = stored.get("elapsed_ms") or 0
    response.truncated = bool(stored.get("truncated"))
    response.error = stored.get("error")
    return response


def interesting(result):
    """The results worth a human's attention: a difference, and not a duplicate."""
    return (result.difference is not None
            and result.difference["difference_count"] > 0
            and not result.duplicate_of
            and not result.error)


def report_lines(run_state, limit=20):
    """A readable summary. States what ran and what it means — and what it does not."""
    summary = run_state.summary()
    lines = [
        f"Fuzzing run: {summary['executed']} of {summary['planned']} mutations executed, "
        f"{summary['requests_sent']} requests sent (budget {summary['budget']})",
        f"  statuses        : {summary['by_status']}",
        f"  duplicates       : {summary['duplicates_skipped']} skipped as identical",
        f"  differences      : {summary['differences_observed']} observable response difference(s)",
    ]
    if summary["cancelled"]:
        lines.append("  cancelled        : yes — partial results retained")
    shown = 0
    for result in run_state.results:
        if not interesting(result):
            continue
        shown += 1
        if shown > limit:
            lines.append(f"  ... {summary['differences_observed'] - limit} more")
            break
        mutation = result.mutation.as_dict()
        lines.append(f"  [{result.index:03d}] {mutation['kind']}:{mutation['target']} "
                     f":{mutation['mode']} -> status {result.status}, "
                     f"{result.difference['difference_count']} section(s) differ")
    lines.append("")
    lines.append("  A difference is not a finding, and a run with none is coverage,")
    lines.append("  not clearance. Validate before reporting a defect as reproduced.")
    return "\n".join(lines)
