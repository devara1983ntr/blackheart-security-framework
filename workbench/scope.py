"""The authorization gate. Every active request in this workbench passes here.

Why this module exists
----------------------
The rest of the workbench can send HTTP requests to a target. That is a real
capability with real consequences, and the repository's own position on it has
always been that the danger is not the request — it is a request nobody
authorised. So authorization is not a flag a caller may set, or a default that
can be edited: it is a file, `scope.json`, that a human writes and signs by
naming the hosts, paths and methods they are willing to have touched, and this
module is the only thing in the codebase that decides whether a request may
leave the process.

Design rules, and why each one is load-bearing:

* **Fail closed.** An unreadable file, an unknown key, a missing field, an empty
  host list or an empty method list all refuse *everything*. A configuration
  error must never widen access; the failure mode has to be a refusal, because
  the alternative is "it ran and did something" with nothing to point at.
* **No bypass.** There is no `--ignore-scope`, no environment variable, no
  keyword argument and no subclass hook that turns a check off. `ScopeGuard`
  exposes no method that relaxes anything, and unknown keys in the file are
  rejected rather than ignored — that is what makes `"ignore_scope": true` a
  parse error instead of a silent, plausible-looking override.
* **Exclusion beats inclusion.** If a host is both allowed and excluded, it is
  excluded. Ambiguity resolves toward the smaller surface, always.
* **Time is part of scope.** Authorization expires. `authorized_until` is
  honest about engagements that end.
* **Budgets are scope, not tuning.** A request ceiling, a concurrency ceiling
  and a minimum interval are part of what the authoriser agreed to, so they live
  in the same file as the hosts and are enforced in the same gate.

What this does **not** do: it does not decide whether an argument is *wise*.
Scope is a ceiling, not a strategy. A target inside scope can still be damaged
by a careless request, which is why the workbench's write methods are disabled
unless the scope names them and each one is confirmed at the call site.
"""

from __future__ import annotations

import datetime as _dt
import ipaddress
import json
import os
import re
import socket
import time
import urllib.parse

# Methods that cannot be sent unless the scope names them *and* the caller
# passes an explicit confirmation. The gate itself enforces the scope list; the
# confirmation is enforced in http_client so that a scope wide enough to allow
# writes still cannot be walked into by accident.
READ_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

KNOWN_KEYS = {
    "targets", "allowed_hosts", "allowed_paths", "excluded_hosts",
    "excluded_paths", "allowed_methods", "max_requests", "max_concurrency",
    "max_response_bytes", "max_redirects", "timeout_s", "min_interval_s",
    "authorized_until", "allow_private_networks", "notes",
}

# Keys that look like an attempt to switch a control off. They are not valid
# configuration; naming them explicitly means the error message says *why*
# rather than the generic "unknown key".
FORBIDDEN_KEYS = {
    "ignore_scope", "bypass", "bypass_scope", "no_scope", "disable_scope",
    "skip_scope", "force", "unsafe", "allow_all", "any_host", "wildcard",
    "ignore_authorization", "disable_checks",
}

DEFAULT_LIMITS = {
    "max_requests": 0,
    "max_concurrency": 1,
    "max_response_bytes": 5_000_000,
    "max_redirects": 5,
    "timeout_s": 10.0,
    "min_interval_s": 1.0,
}


class ScopeError(Exception):
    """Raised when a request is refused, or when a scope file is unusable.

    One exception type for both, deliberately: a caller that swallows "the
    config was bad" and a caller that swallows "the target was out of scope"
    are making the same mistake, and they should have to write the same
    except clause to make it.
    """


def _now_utc():
    return _dt.datetime.now(_dt.timezone.utc)


def _parse_until(value):
    """`authorized_until` is an ISO-8601 date or timestamp in UTC.

    A date means the end of that day, because "authorized until the 14th"
    should not mean the start of the 14th.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ScopeError("authorized_until must be an ISO-8601 date string")
    text = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            d = _dt.datetime.strptime(text, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=_dt.timezone.utc)
            return d
        d = _dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=_dt.timezone.utc)
        return d
    except ValueError as exc:
        raise ScopeError(f"authorized_until is not a valid ISO-8601 date: {value!r}") from exc


def _is_ip_literal(host):
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def address_is_private(addr):
    """True for anything that is not a globally routable unicast address.

    Covers loopback, RFC1918, link-local, multicast, reserved, unspecified and
    IPv6 unique-local — the ranges an SSRF reaches for. `is_global` handles
    IPv6 and the RFC 5737 documentation ranges that a hand-written prefix list
    reliably gets wrong.

    `is_global` alone is not sufficient: `224.0.0.1` reports as global, because
    the stdlib's private-range table does not cover multicast. A test caught
    that, which is why this predicate is asserted against the whole range table
    rather than a couple of examples.
    """
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return True          # unparseable is treated as unsafe
    return ip.is_multicast or not ip.is_global


class Scope:
    """A parsed, validated authorization ceiling. Immutable by convention."""

    def __init__(self, data, source="<memory>"):
        if not isinstance(data, dict):
            raise ScopeError("scope must be a JSON object")
        self.source = source

        unknown = sorted(set(data) - KNOWN_KEYS)
        if unknown:
            forbidden = sorted(set(unknown) & FORBIDDEN_KEYS)
            if forbidden:
                raise ScopeError(
                    "scope contains a key that would disable a control "
                    f"({', '.join(forbidden)}). There is no bypass: remove it, "
                    "or do not run this against the target.")
            raise ScopeError(f"unknown scope key(s): {', '.join(unknown)}")

        def str_list(key):
            value = data.get(key, [])
            if value is None:
                return []
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ScopeError(f"{key} must be a list of strings")
            return [v.strip() for v in value if v.strip()]

        self.targets = str_list("targets")
        self.allowed_hosts = [h.lower() for h in str_list("allowed_hosts")]
        self.allowed_paths = str_list("allowed_paths")
        self.excluded_hosts = [h.lower() for h in str_list("excluded_hosts")]
        self.excluded_paths = str_list("excluded_paths")
        self.methods = tuple(m.upper() for m in str_list("allowed_methods"))
        self.notes = data.get("notes", "")
        if not isinstance(self.notes, str):
            raise ScopeError("notes must be a string")

        bad_methods = [m for m in self.methods
                       if not re.fullmatch(r"[A-Z]{3,10}", m)]
        if bad_methods:
            raise ScopeError(f"invalid HTTP method(s) in allowed_methods: {bad_methods}")

        for key, default in DEFAULT_LIMITS.items():
            value = data.get(key, default)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ScopeError(f"{key} must be a number")
            if value < 0:
                raise ScopeError(f"{key} must not be negative")
            setattr(self, key, float(value) if key in ("timeout_s", "min_interval_s") else int(value))
        self.max_requests = int(self.max_requests)
        self.max_concurrency = max(1, int(self.max_concurrency)) if self.max_concurrency else 1

        self.allow_private_networks = data.get("allow_private_networks", False)
        if not isinstance(self.allow_private_networks, bool):
            raise ScopeError("allow_private_networks must be true or false")

        self.authorized_until = _parse_until(data.get("authorized_until"))

        if not self.allowed_hosts:
            raise ScopeError(
                "allowed_hosts is empty: a scope that names no host authorizes "
                "nothing. Add the hosts you are authorized to test.")
        if not self.methods:
            raise ScopeError(
                "allowed_methods is empty: a scope that names no method "
                "authorizes nothing. Add the methods that were agreed.")
        if self.max_requests <= 0:
            raise ScopeError(
                "max_requests must be a positive number: an unbounded request "
                "budget is not a scope.")

    # -- host and path matching ------------------------------------------
    def host_allowed(self, host):
        """Exact match, or a subdomain wildcard written `*.example.com`.

        The wildcard matches subdomains only, and never a bare suffix: allowing
        `*.example.com` must not allow `notexample.com`.
        """
        host = (host or "").lower().rstrip(".")
        if not host:
            return False
        if self._host_excluded(host):
            return False
        for pattern in self.allowed_hosts:
            if pattern == host:
                return True
            if pattern.startswith("*."):
                suffix = pattern[2:]
                if host.endswith("." + suffix):
                    return True
        return False

    def _host_excluded(self, host):
        for pattern in self.excluded_hosts:
            if pattern == host:
                return True
            if pattern.startswith("*.") and host.endswith("." + pattern[2:]):
                return True
        return False

    def path_allowed(self, path):
        path = path or "/"
        for pattern in self.excluded_paths:
            if _path_matches(pattern, path):
                return False
        if not self.allowed_paths:
            return True                      # host-scoped, no path restriction
        return any(_path_matches(p, path) for p in self.allowed_paths)

    def method_allowed(self, method):
        return (method or "").upper() in self.methods


def _path_matches(pattern, path):
    """Prefix match, with `*` as a within-segment wildcard.

    A prefix match is what an engagement actually agrees to ("the /api tree"),
    and `*` covers the case that needs it without pulling in a glob engine that
    also matches across separators in surprising ways.
    """
    if pattern.endswith("*") and not pattern.endswith("**"):
        pattern = pattern[:-1]
    if "*" in pattern:
        rx = "^" + "".join(".*" if c == "*" else re.escape(c) for c in pattern)
        return re.match(rx, path) is not None
    return path == pattern or path.startswith(pattern.rstrip("/") + "/") or path == pattern.rstrip("/")


def load_scope(path):
    """Read and validate a scope file. A missing file is not a default scope."""
    if not path or not os.path.isfile(path):
        raise ScopeError(f"scope file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ScopeError(f"{path} is not valid JSON: {exc}") from exc
    else:
        if not isinstance(data, dict) or not data:
            raise ScopeError(f"{path} is empty: an empty scope authorizes nothing")
    return Scope(data, source=path)


class Decision:
    __slots__ = ("allowed", "reason", "rule", "url", "method")

    def __init__(self, allowed, reason="", rule="", url="", method=""):
        self.allowed = allowed
        self.reason = reason
        self.rule = rule
        self.url = url
        self.method = method

    def __bool__(self):
        return self.allowed

    def as_dict(self):
        return {"allowed": self.allowed, "reason": self.reason,
                "rule": self.rule, "url": self.url, "method": self.method}


class ScopeGuard:
    """The single choke point. Nothing active may bypass it.

    `resolve` is injected so tests can exercise DNS-dependent decisions
    deterministically; in production it is `socket.getaddrinfo`.
    """

    def __init__(self, scope, clock=time.monotonic, utcnow=_now_utc, resolve=None):
        self.scope = scope
        self._clock = clock
        self._utcnow = utcnow
        self._resolve = resolve or _default_resolve
        self.requests_made = 0
        self.denials = []
        self._last_request_at = 0.0

    # -- checks ----------------------------------------------------------
    def check(self, url, method="GET", *, resolve=True):
        """Decide one request. Returns a Decision; never raises for a refusal."""
        url = (url or "").strip()
        method = (method or "GET").upper()
        parsed = urllib.parse.urlsplit(url)

        if parsed.scheme not in ("http", "https"):
            return self._deny("scheme", f"scheme {parsed.scheme or '(none)'!r} is not "
                                        f"http or https", url, method)
        if not parsed.hostname:
            return self._deny("host", "URL has no host", url, method)
        if parsed.username or parsed.password:
            return self._deny("credentials", "credentials in the URL are refused; "
                                             "supply them through the credential reference, not the URL",
                              url, method)

        if not self.scope.host_allowed(parsed.hostname):
            return self._deny("host", f"{parsed.hostname} is not in allowed_hosts",
                              url, method)
        if not self.scope.path_allowed(parsed.path or "/"):
            return self._deny("path", f"{parsed.path or '/'} is not in allowed_paths "
                                      f"(or matches an exclusion)", url, method)
        if not self.scope.method_allowed(method):
            return self._deny("method", f"{method} is not in allowed_methods",
                              url, method)

        until = self.scope.authorized_until
        if until is not None and self._utcnow() > until:
            return self._deny("expired",
                              f"authorization expired at {until.isoformat()}",
                              url, method)

        if self.requests_made >= self.scope.max_requests:
            return self._deny("budget",
                              f"request budget exhausted ({self.scope.max_requests})",
                              url, method)

        if resolve:
            ip_decision = self.check_address(parsed.hostname, url=url, method=method)
            if not ip_decision:
                return ip_decision

        return Decision(True, "within scope", "allowed", url, method)

    def check_address(self, host, url="", method="GET"):
        """Resolve and vet the destination address.

        This is the SSRF control and the DNS-rebinding control in one place.
        The address is checked *before* a connection is opened, and the address
        that was checked is the address that is used — the client connects to
        the vetted IP with the original Host header, so a second resolution
        between check and connect cannot move the request.
        """
        if _is_ip_literal(host):
            addrs = [host.strip("[]")]
        else:
            try:
                addrs = self._resolve(host)
            except Exception as exc:
                return self._deny("dns", f"could not resolve {host}: {type(exc).__name__}",
                                  url, method)
            if not addrs:
                return self._deny("dns", f"{host} did not resolve", url, method)

        private = [a for a in addrs if address_is_private(a)]
        if private:
            if not self.scope.allow_private_networks:
                return self._deny(
                    "address",
                    f"{host} resolves to a non-public address ({private[0]}); "
                    f"private, loopback and link-local destinations are refused",
                    url, method)
            # Even when private destinations are authorized, the host must have
            # been named. allow_private_networks widens the address space, never
            # the host list.
            if not self.scope.host_allowed(host):
                return self._deny("address",
                                  f"{host} is not in allowed_hosts", url, method)
        return Decision(True, "address within scope", "allowed", url, method)

    # -- accounting ------------------------------------------------------
    def note_request(self):
        self.requests_made += 1
        self._last_request_at = self._clock()

    def wait_for_rate_limit(self, sleeper=time.sleep):
        """Space requests out. The interval is part of the scope file."""
        gap = self.scope.min_interval_s
        if gap <= 0:
            return 0.0
        waited = 0.0
        if self._last_request_at:
            elapsed = self._clock() - self._last_request_at
            if elapsed < gap:
                waited = gap - elapsed
                sleeper(waited)
        return waited

    def _deny(self, rule, reason, url="", method=""):
        decision = Decision(False, reason, rule, url, method)
        self.denials.append(decision.as_dict())
        return decision

    # -- reporting -------------------------------------------------------
    def summary(self):
        return {
            "scope_file": self.scope.source,
            "allowed_hosts": list(self.scope.allowed_hosts),
            "allowed_paths": list(self.scope.allowed_paths),
            "allowed_methods": list(self.scope.methods),
            "max_requests": self.scope.max_requests,
            "max_concurrency": self.scope.max_concurrency,
            "authorized_until": (self.scope.authorized_until.isoformat()
                                 if self.scope.authorized_until else None),
            "requests_made": self.requests_made,
            "denials": len(self.denials),
        }


def _default_resolve(host):
    infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    out = []
    for info in infos:
        addr = info[4][0]
        if addr not in out:
            out.append(addr)
    return out


def require(guard, url, method="GET", *, confirm_write=False):
    """The call-site helper every active module uses.

    Raises `ScopeError` when the request may not be made, so a refusal cannot be
    ignored by accident: there is no falsy return to forget to check. Write
    methods additionally require `confirm_write=True`, which no command sets
    except the one documented as doing so.
    """
    decision = guard.check(url, method)
    if not decision:
        raise ScopeError(f"{method} {url} refused [{decision.rule}]: {decision.reason}")
    if method.upper() in WRITE_METHODS and not confirm_write:
        raise ScopeError(
            f"{method} {url} changes state on the target and scope alone is not "
            f"enough: pass an explicit confirmation at the call site")
    return decision
