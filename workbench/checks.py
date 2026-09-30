"""Observable security checks.

What these are
--------------
Readings of responses the operator already captured. A check compares what came
back against a stated expectation and writes down the difference — a missing
`Strict-Transport-Security`, a cookie without `HttpOnly`, a `Location` header
that echoes a query parameter. None of them sends an exploit, and none of them
escalates: the strongest thing a check may produce is a `POTENTIAL` record, and a
`POTENTIAL` record may not use the language of a validated defect (enforced in
`evidence.py`).

Why so careful about the wording
--------------------------------
Because "a header is missing" and "this page can be framed by another site" are
the same observation dressed very differently, and only one of them is honest. A header
can be absent because a reverse proxy adds it, because the endpoint is an API
that never renders, or because the application is a static file. The check
reports the observation and states what would have to be true for it to matter.
That is a slower sentence to write and the only one worth attaching to a report.

Two checks need evidence the workbench cannot produce by itself — an
authorization-boundary comparison needs two identities, and a rate-limit
behaviour check needs a burst. Both are implemented as comparisons over records
the operator supplies, and both refuse to produce a record at all without that
input, rather than guessing.
"""

from __future__ import annotations

import json
import re

from . import diff as diffmod
from . import evidence as ev
from . import http_client as hc

# The response headers this framework treats as the baseline, with the case each
# one addresses. Absence is an observation, not a defect — see the limitations
# written into every record below.
BASELINE_HEADERS = {
    "strict-transport-security": "transport security enforcement is browser-enforced and cannot be downgraded without it",
    "content-security-policy": "the browser's own injection surface is unbounded without it",
    "x-content-type-options": "content-type sniffing can turn a document into a script",
    "x-frame-options": "the page can be framed by another origin without it (CSP frame-ancestors also addresses this)",
    "referrer-policy": "referrer leakage to third parties is unbounded without it",
}

BANNER_HEADERS = ("server", "x-powered-by", "x-aspnet-version", "x-generator")

ERROR_SIGNATURES = (
    (r"Traceback \(most recent call last\)", "Python traceback"),
    (r"\bat [a-z]+\.[a-z]+\.[A-Z][A-Za-z]+", "Java stack frame"),
    (r"Microsoft OLE DB Provider|ODBC SQL Server Driver", "database driver banner"),
    (r"You have an error in your SQL syntax", "SQL error text"),
    (r"Warning: [a-z_]+\(\) expects parameter", "PHP warning"),
    (r"(/var/www/|/home/\w+/|C:\\\\inetpub\\)", "server filesystem path"),
    (r"at Object\.<anonymous> \(", "Node.js stack frame"),
    (r"<b>Fatal error</b>:", "PHP fatal error"),
)

WEAK_TLS_VERSIONS = ("TLSv1", "TLSv1.1", "SSLv2", "SSLv3")
WEAK_CIPHER_MARKERS = ("RC4", "3DES", "DES-CBC3", "NULL", "EXPORT", "MD5")

# Query-parameter names whose value is commonly placed into a redirect.
REDIRECT_PARAMETER_NAMES = ("next", "url", "redirect", "redirect_uri", "return",
                            "returnurl", "return_url", "continue", "target",
                            "dest", "destination", "goto", "out", "link", "to")


def _scope_summary(scope_summary):
    return scope_summary or {}


def _request_of(record):
    return {
        "method": record.get("method"),
        "url": record.get("url"),
        "headers": hc.redact_headers(record.get("request_headers") or {}),
        "body": (record.get("request_body") or "")[:4000],
    }


def _response_of(record):
    response = (record or {}).get("response") or {}
    return {
        "status": response.get("status"),
        "headers": hc.redact_headers(response.get("headers") or {}),
        "content_type": response.get("content_type"),
        "bytes": response.get("bytes"),
        "body_text": (response.get("body_text") or "")[:8000],
    }


def _reproduction(record, note):
    """The steps a person would follow to see this for themselves."""
    request = _request_of(record)
    return [
        f"1. Send the captured request unchanged: {request['method']} {request['url']}",
        f"2. Reason to look: {note}",
        "3. Compare the response against the expectation recorded in this finding.",
        "4. If the observation is about impact rather than existence, that step is "
        "not performed by this tool: validate it manually under the engagement's "
        "rules before reporting a defect as validated.",
    ]


def _mk(record, cid, title, *, severity, confidence, status, expected, observed,
        impact, limitations, remediation, notes="", scope_summary=None):
    return ev.Evidence(
        cid, title, severity=severity, confidence=confidence, status=status,
        target=record.get("url", ""), scope=_scope_summary(scope_summary),
        expected=expected, observed=observed, impact=impact, limitations=limitations,
        remediation=remediation, request=_request_of(record),
        response=_response_of(record),
        reproduction=_reproduction(record, observed[:200]),
        notes=notes,
        provenance=ev.provenance_for(_scope_summary(scope_summary),
                                     extra={"check": cid, "source_record": record.get("id")}),
    )


# ------------------------------------------------------------ HTTP properties
def security_headers(record, cid="E-HEADERS", scope_summary=None):
    """Baseline response headers, and banners that disclose the stack."""
    out = []
    if not isinstance((record.get("response") or {}).get("status"), int):
        return out
    headers = {k.lower(): v for k, v in
               ((record.get("response") or {}).get("headers") or {}).items()}
    absent = [name for name in BASELINE_HEADERS if name not in headers]
    if absent:
        out.append(_mk(
            record, f"{cid}-ABSENT",
            f"Response headers absent from the baseline: {', '.join(absent)}",
            severity="informational", confidence="high", status="OBSERVED",
            expected="The response carries the headers the assessment baseline expects.",
            observed=f"These headers were not present: {', '.join(absent)}.",
            impact=("Each missing header removes one browser-enforced control for this "
                    "response. Whether that matters depends on what the endpoint does: "
                    "an API returning JSON renders nothing, and a header a front-end "
                    "proxy adds will not appear here."),
            limitations=("Absence of a header in one response is not a defect and does not "
                         "establish exposure. Headers may be added upstream of the "
                         "captured hop, on a different route, or for a different content "
                         "type. Confirm on the deployed edge before treating any of these "
                         "as remediation work."),
            remediation=("Add the headers at the edge that terminates TLS, then re-capture "
                         "this response and confirm they arrive on the final hop."),
            notes=f"Baseline set: {', '.join(sorted(BASELINE_HEADERS))}",
            scope_summary=scope_summary))
    banners = {name: headers[name] for name in BANNER_HEADERS if name in headers}
    if banners:
        out.append(_mk(
            record, f"{cid}-BANNER",
            f"Technology disclosure in response headers: {', '.join(sorted(banners))}",
            severity="informational", confidence="high", status="OBSERVED",
            expected="Response headers do not name the software and version serving them.",
            observed=f"Disclosed: {json.dumps(banners, sort_keys=True)}",
            impact=("Version banners narrow the search an attacker has to do. They are "
                    "fuel for targeted reconnaissance rather than a weakness "
                    "on its own."),
            limitations=("A banner may be absent from this hop and present at the edge, or "
                         "deliberately generic. Do not infer an unpatched version from a "
                         "banner; confirm with the asset owner."),
            remediation="Suppress or genericise the banner at the reverse proxy.",
            scope_summary=scope_summary))
    return out


def cookie_flags(record, cid="E-COOKIE", scope_summary=None):
    """`Set-Cookie` without the flags that constrain a cookie's exposure."""
    out = []
    headers = ((record.get("response") or {}).get("headers") or {})
    raw = [v for k, v in headers.items() if k.lower() == "set-cookie"]
    for value in raw:
        parsed = diffmod.parse_cookies([value])
        for name, cookie in parsed.items():
            attrs = cookie["attributes"]
            missing = [flag for flag in ("httponly", "secure", "samesite")
                       if flag not in attrs]
            if not missing:
                continue
            same_site_none_secure = (str(attrs.get("samesite", "")).lower() == "none"
                                     and "secure" not in attrs)
            out.append(_mk(
                record, f"{cid}-{_slug(name)}",
                f"Cookie attribute(s) absent: {name} ({', '.join(missing)})",
                severity="low" if "httponly" not in missing or "secure" not in missing
                else "informational",
                confidence="high", status="OBSERVED",
                expected="Session cookies are set with HttpOnly, Secure and an explicit SameSite.",
                observed=(f"Cookie {name!r} was set without: {', '.join(missing)}."
                          + (" SameSite=None was set without Secure, which browsers "
                             "reject or ignore." if same_site_none_secure else "")),
                impact=("A cookie readable by script is reachable from any injected script; "
                        "a cookie sent over plaintext is reachable from the network; a "
                        "cookie without SameSite is sent on cross-site navigations."),
                limitations=("Whether these matter depends on the cookie's purpose. A "
                             "consent or theme cookie needs none of them; a session cookie "
                             "needs all three. This check does not know which this is, and "
                             "does not read the value."),
                remediation=("Set session cookies with HttpOnly; Secure; SameSite=Lax or "
                             "Strict, and confirm the attribute survives the CDN."),
                scope_summary=scope_summary))
    return out


def cors_configuration(record, cid="E-CORS", scope_summary=None):
    """CORS responses that broaden who may read the response."""
    headers = {k.lower(): v for k, v in
               ((record.get("response") or {}).get("headers") or {}).items()}
    origin = headers.get("access-control-allow-origin", "")
    credentials = str(headers.get("access-control-allow-credentials", "")).lower() == "true"
    request_origin = ""
    for name, value in ((record.get("request_headers") or {}).items()):
        if name.lower() == "origin":
            request_origin = value
    if not origin:
        return []
    if origin == "*":
        return [_mk(
            record, f"{cid}-WILDCARD",
            "CORS allows any origin" + (" with credentials" if credentials else ""),
            severity="medium" if credentials else "low",
            confidence="high", status="OBSERVED",
            expected="Cross-origin read access is limited to the origins that need it.",
            observed=(f"Access-Control-Allow-Origin: * "
                      f"(Allow-Credentials: {str(credentials).lower()})"),
            impact=("Any site can read this response from a browser the user visits. With "
                    "credentials allowed the read is in the user's authenticated context."
                    if credentials else
                    "Any site can read this response from a browser the user visits."),
            limitations=("If the response never varies with the caller and carries no user "
                         "data, a wildcard is a legitimate configuration and nothing here "
                         "applies. This record states the configuration, not its effect."),
            remediation=("Echo a validated origin from an allowlist instead of `*`, and do "
                         "not combine a wildcard with credentials."),
            scope_summary=scope_summary)]
    if credentials and request_origin and origin == request_origin:
        return [_mk(
            record, f"{cid}-REFLECTED",
            "CORS reflects the request Origin with credentials allowed",
            severity="low", confidence="medium", status="POTENTIAL",
            expected="Reflected origins are validated against an allowlist.",
            observed=f"Origin {request_origin!r} was reflected as the allowed origin "
                     f"with Allow-Credentials: true.",
            impact=("If the reflection is not validated against a list, any origin that "
                    "sends this request receives the reflection and can read the response "
                    "in the user's context."),
            limitations=("A single reflected origin does not establish that arbitrary "
                         "origins are reflected: many implementations echo any origin, and "
                         "many echo only listed ones. Testing with a second, unrelated "
                         "origin is required and is a deliberate authorization decision."),
            remediation="Validate the origin against an explicit allowlist before echoing.",
            scope_summary=scope_summary)]
    return []


def cache_of_authenticated_response(record, cid="E-CACHE", scope_summary=None):
    """A response to a credentialed request that permits shared caching."""
    request_headers = {k.lower(): v for k, v in
                       ((record.get("request_headers") or {}).items())}
    credentialed = any(name in request_headers
                       for name in ("authorization", "cookie"))
    response_headers = {k.lower(): v for k, v in
                        ((record.get("response") or {}).get("headers") or {}).items()}
    cache_control = str(response_headers.get("cache-control", "")).lower()
    if not credentialed or "public" not in cache_control:
        return []
    return [_mk(
        record, f"{cid}-PUBLIC",
        "A credentialed request received a publicly cacheable response",
        severity="low", confidence="medium", status="POTENTIAL",
        expected="Responses to authenticated requests are marked private or no-store.",
        observed=f"Request carried credentials and the response set Cache-Control: "
                 f"{response_headers.get('cache-control')}.",
        impact=("A shared cache may store the response and serve it to another user. "
                "Whether that happens depends on the cache and on whether the response "
                "varies by user."),
        limitations=("This is a header-level observation. It does not establish that any "
                     "cache stored or served the response, and it does not show that the "
                     "response contains user data. Confirming impact requires a request "
                     "without credentials through the same cache — a deliberate step, not "
                     "one this check takes."),
        remediation="Mark authenticated responses private or no-store, and set Vary "
                    "appropriately if the response varies by header.",
        scope_summary=scope_summary)]


def content_type_handling(record, cid="E-CTYPE", scope_summary=None):
    """Declared type against the bytes, and the sniffing control."""
    response = (record.get("response") or {})
    headers = {k.lower(): v for k, v in (response.get("headers") or {}).items()}
    declared = (response.get("content_type") or "").lower()
    body = (response.get("body_text") or "")
    nosniff = str(headers.get("x-content-type-options", "")).lower()
    looks_html = bool(re.search(r"<html|<!doctype html", body[:2000], re.I))
    out = []
    if looks_html and "html" not in declared:
        out.append(_mk(
            record, f"{cid}-MISMATCH",
            "Response body is HTML but the declared content type is not",
            severity="low", confidence="high", status="OBSERVED",
            expected="The declared content type describes the bytes that follow.",
            observed=f"Declared {declared or '(none)'}; the body's first bytes are HTML.",
            impact=("A browser that sniffs rather than honouring the declaration may render "
                    "the document, which turns a stored file into a page in the site's "
                    "origin."),
            limitations=("Sniffing behaviour is browser-specific and is suppressed by "
                         "X-Content-Type-Options: nosniff, which this response "
                         f"{'sets' if nosniff == 'nosniff' else 'does not set'}. "
                         "This is a document-handling observation, not a defect in itself."),
            remediation="Declare the type that matches the bytes, and send "
                        "X-Content-Type-Options: nosniff.",
            scope_summary=scope_summary))
    elif looks_html and "nosniff" not in nosniff:
        out.append(_mk(
            record, f"{cid}-NOSNIFF",
            "HTML response without X-Content-Type-Options: nosniff",
            severity="informational", confidence="high", status="OBSERVED",
            expected="Sniffing is disabled on responses that could be misread.",
            observed="The response is HTML and does not set X-Content-Type-Options.",
            impact="Removes one browser-side control against content-type confusion.",
            limitations=("Impact requires a path where attacker-controlled bytes are "
                         "served from this origin. On a static documentation origin there "
                         "is no such path."),
            remediation="Send X-Content-Type-Options: nosniff on all responses.",
            scope_summary=scope_summary))
    return out


def redirect_behavior(record, cid="E-REDIRECT", scope_summary=None):
    """Redirect hops that leave the origin, or downgrade the scheme."""
    out = []
    chain = record.get("redirect_chain") or []
    if not chain:
        return out
    first = record.get("host") or ""
    for hop in chain:
        location = hop.get("location", "")
        host = ""
        try:
            from urllib.parse import urlsplit
            host = urlsplit(location).hostname or ""
        except Exception:
            host = ""
        if location.lower().startswith("http://") and first and not location.startswith("http://" + first):
            out.append(_mk(
                record, f"{cid}-DOWNGRADE-{_slug(host or first)}",
                "Redirect to a plaintext URL",
                severity="low", confidence="high", status="OBSERVED",
                expected="Redirects preserve the transport security of the original request.",
                observed=f"Redirect to {location!r} (status {hop.get('status')}).",
                impact="The redirected request travels without transport protection.",
                limitations=("A redirect to http is sometimes intentional for a legacy "
                             "host. Whether it is reachable from an authenticated flow "
                             "determines whether it matters."),
                remediation="Redirect to https, and enable HSTS so the downgrade is not "
                            "available to an interceptor.",
                scope_summary=scope_summary))
        if host and host != first:
            out.append(_mk(
                record, f"{cid}-EXTERNAL-{_slug(host)}",
                f"Redirect leaves the origin: {host}",
                severity="informational", confidence="high", status="OBSERVED",
                expected="Redirects stay within the assessed origin.",
                observed=f"Hop from {hop.get('from')} to {location} ({host}).",
                impact="Cross-origin redirects widen the assessed surface and are where "
                       "open-redirect conditions are usually found.",
                limitations=("A redirect to a documented identity provider or CDN is "
                             "normal. This record names the hop; it does not judge it."),
                remediation="Confirm the destination is intended, and that it is built "
                            "from a fixed value rather than from user input.",
                scope_summary=scope_summary))
    return out


def tls_indicators(record, cid="E-TLS", scope_summary=None):
    """Protocol version, cipher and certificate observations from the handshake."""
    tls = ((record.get("response") or {}).get("tls")) or {}
    if not tls:
        return []
    out = []
    version = tls.get("version") or ""
    if version in WEAK_TLS_VERSIONS:
        out.append(_mk(
            record, f"{cid}-VERSION",
            f"Obsolete TLS version negotiated: {version}",
            severity="medium", confidence="high", status="OBSERVED",
            expected="TLS 1.2 or newer.",
            observed=f"The handshake completed with {version}.",
            impact="Obsolete protocol versions have known practical weaknesses.",
            limitations=("The negotiation may reflect this client's capabilities rather "
                         "than the server's policy. Confirm with a scanner that offers "
                         "only modern versions before treating it as the server's floor."),
            remediation="Raise the minimum accepted version to TLS 1.2, then 1.3.",
            scope_summary=scope_summary))
    cipher = tls.get("cipher") or ""
    if any(marker in cipher.upper() for marker in WEAK_CIPHER_MARKERS):
        out.append(_mk(
            record, f"{cid}-CIPHER",
            f"Weak cipher suite negotiated: {cipher}",
            severity="medium", confidence="high", status="OBSERVED",
            expected="A modern AEAD cipher suite.",
            observed=f"The handshake completed with {cipher}.",
            impact="Weak or export-grade ciphers can be attacked in practice.",
            limitations="As above: this is one negotiation, not the server's whole policy.",
            remediation="Restrict the cipher list to modern AEAD suites.",
            scope_summary=scope_summary))
    return out


def error_disclosure(record, cid="E-ERROR", scope_summary=None):
    """Error text that names internals."""
    response = (record.get("response") or {})
    body = response.get("body_text") or ""
    status = response.get("status")
    if not isinstance(status, int) or status < 400:
        return []
    found = []
    for pattern, label in ERROR_SIGNATURES:
        match = re.search(pattern, body)
        if match:
            found.append((label, match.group(0)[:80]))
    if not found:
        return []
    labels = ", ".join(label for label, _ in found)
    return [_mk(
        record, f"{cid}-DISCLOSURE",
        f"Error response discloses internals: {labels}",
        severity="low", confidence="high", status="OBSERVED",
        expected="Error responses state that the request failed without naming internals.",
        observed=f"Status {status} with: " + "; ".join(f"{label} ({sample!r})"
                                                       for label, sample in found),
        impact=("Framework versions, file paths, query fragments and stack frames help an "
                "attacker target the next step and can expose the data model."),
        limitations=("Detailed errors in a development environment are expected. Whether "
                     "this response is reachable in production, and whether it is reachable "
                     "without authentication, is a separate question this check cannot "
                     "answer from one response."),
        remediation="Return a generic error to the client; keep the detail in server-side "
                    "logs correlated by a request id.",
        scope_summary=scope_summary)]


def reflected_input(record, cid="E-REFLECT", scope_summary=None):
    """A parameter value appearing verbatim in an HTML response.

    This is an *indicator*. Reflection is a necessary condition for reflected
    script execution and is not sufficient for it: the check does not attempt to
    make anything execute, and the record says so in the limitations that a
    reader cannot miss.
    """
    from urllib.parse import parse_qsl, urlsplit
    response = (record.get("response") or {})
    body = response.get("body_text") or ""
    content_type = (response.get("content_type") or "").lower()
    if "html" not in content_type or not body:
        return []
    query = urlsplit(record.get("url") or "").query
    hits = []
    for name, value in parse_qsl(query, keep_blank_values=True):
        if len(value) < 3:
            continue
        if value in body:
            index = body.find(value)
            hits.append({"parameter": name, "value": value[:60],
                         "context": body[max(0, index - 30):index + len(value) + 30]})
    if not hits:
        return []
    return [_mk(
        record, f"{cid}-INDICATOR",
        f"Query parameter reflected verbatim in an HTML response: "
        f"{', '.join(h['parameter'] for h in hits)}",
        severity="informational", confidence="high", status="POTENTIAL",
        expected="User input placed into HTML is encoded for the context it lands in.",
        observed="; ".join(f"{h['parameter']}={h['value']!r} appears in the body near "
                           f"{h['context']!r}" for h in hits[:4]),
        impact=("Reflection is the delivery mechanism for reflected script execution. "
                "Without context-appropriate encoding, a value a browser interprets as "
                "markup or script runs in the site's origin."),
        limitations=("Reflection alone is not execution. This check does not send a "
                     "payload, does not attempt to break out of the surrounding context, "
                     "and cannot see what a browser would do with the value — server-side, "
                     "proxy and browser-side filtering are all invisible from here. "
                     "Establishing impact requires a deliberate, manual test under the "
                     "engagement's rules."),
        remediation=("Encode on output for the destination context (HTML body vs attribute "
                     "vs JavaScript), and prefer a templating engine's contextual escaping "
                     "over hand-rolled sanitisation."),
        scope_summary=scope_summary)]


def open_redirect_indicator(record, cid="E-OPENREDIR", scope_summary=None):
    """A redirect whose target traces back to a query parameter."""
    from urllib.parse import parse_qsl, urlsplit
    chain = record.get("redirect_chain") or []
    if not chain:
        return []
    query = dict(parse_qsl(urlsplit(record.get("url") or "").query))
    out = []
    for hop in chain:
        location = hop.get("location") or ""
        for name, value in query.items():
            if not value or len(value) < 4:
                continue
            if value in location or (name.lower() in REDIRECT_PARAMETER_NAMES
                                     and location.rstrip("/").endswith(value.rstrip("/"))):
                out.append(_mk(
                    record, f"{cid}-{_slug(name)}",
                    f"Redirect target appears to come from the {name!r} parameter",
                    severity="low", confidence="medium", status="POTENTIAL",
                    expected="Redirect destinations are chosen from fixed values, not input.",
                    observed=f"Location {location!r} contains the value supplied in "
                             f"{name!r}.",
                    impact=("An attacker who can supply that parameter can send a user to a "
                            "destination of their choosing from a trusted link, and can "
                            "carry credential-bearing fragments across origins."),
                    limitations=("The parameter may be validated against an allowlist "
                                 "before use, and the value that produced this hop may "
                                 "have been on that list. Testing with an unrelated "
                                 "destination is the step that answers this, and it is a "
                                 "deliberate action rather than something this check does."),
                    remediation="Validate the destination against an allowlist of "
                                "permitted hosts or, better, map identifiers to fixed URLs.",
                    scope_summary=scope_summary))
                break
    return out


def method_handling(record, cid="E-METHODS", scope_summary=None):
    """Write verbs advertised by an OPTIONS response."""
    response = (record.get("response") or {})
    if response.get("status") != 204 and not ((record.get("method") or "").upper() == "OPTIONS"):
        return []
    allow = ""
    for name, value in (response.get("headers") or {}).items():
        if name.lower() == "allow":
            allow = value
    if not allow:
        return []
    verbs = [v.strip().upper() for v in allow.split(",")]
    writes = [v for v in verbs if v in ("POST", "PUT", "PATCH", "DELETE")]
    if not writes:
        return []
    return [_mk(
        record, f"{cid}-ALLOW",
        f"Endpoint advertises write methods: {', '.join(writes)}",
        severity="informational", confidence="high", status="OBSERVED",
        expected="Only the methods the route implements are advertised.",
        observed=f"Allow: {allow}",
        impact=("An advertised write verb is a route worth testing for authorization. "
                "The advertisement is a map, not a defect."),
        limitations=("Advertising a method does not mean it is implemented without "
                     "authorization, and the route may reject the request anyway. This "
                     "record does not test it: sending a write request is a deliberate "
                     "decision recorded separately."),
        remediation="Advertise only implemented methods, and ensure each is authorised "
                    "server-side.",
        scope_summary=scope_summary)]


# ------------------------------------------------------- API-shaped behaviour
def _by_endpoint(records):
    """Group records by the endpoint they address, ignoring case in the path."""
    groups = {}
    for record in records:
        key = ((record.get("method") or "GET").upper(), record.get("url") or "")
        groups.setdefault(key, []).append(record)
    return groups


def rate_limit_behavior(records, cid="E-RATELIMIT", scope_summary=None, minimum=3):
    """Whether a repeated call to ONE endpoint met a limiter.

    The grouping is the point. Ten requests to ten different endpoints say
    nothing about rate limiting, and an earlier version of this check reported
    exactly that: it read a mixed set of records, saw no 429, and produced a
    record about an unthrottled service. It now requires several calls to the
    same endpoint, and produces nothing when it does not have them.
    """
    usable = [r for r in records if isinstance(r, dict)]
    groups = [g for g in _by_endpoint(usable).values() if len(g) >= minimum]
    if not groups:
        return []
    group = max(groups, key=len)
    statuses = [((r.get("response") or {}).get("status")) for r in group]
    limited = [s for s in statuses if s == 429]
    sample = group[0]
    method, url = (sample.get("method") or "GET"), sample.get("url") or ""
    if limited:
        return [_mk(
            sample, f"{cid}-OBSERVED",
            f"Rate limiting observed: {len(limited)} of {len(statuses)} responses were 429",
            severity="informational", confidence="high", status="OBSERVED",
            expected=("Repeated requests to one endpoint are bounded by a limiter rather "
                      "than served indefinitely."),
            observed=(f"{len(limited)} of {len(statuses)} responses to {method} {url} "
                      f"returned 429."),
            impact=("A working limiter is a control. Its presence is recorded as a "
                    "positive observation and as context for what a bounded run can "
                    "conclude."),
            limitations=("This says nothing about whether the limit is per-identity, per "
                         "endpoint or global, nor what the threshold is. It records that "
                         "a limiter answered within this small burst."),
            remediation="No action. Recorded as an observed control.",
            scope_summary=scope_summary)]
    return [_mk(
        sample, f"{cid}-ABSENT",
        f"No rate limiting observed across {len(statuses)} calls to one endpoint",
        severity="informational", confidence="low", status="POTENTIAL",
        expected=("A burst of repeated calls to one endpoint either meets a limiter or is "
                  "documented as unthrottled."),
        observed=(f"None of {len(statuses)} responses to {method} {url} returned 429 "
                  f"(statuses: {sorted(set(str(s) for s in statuses))})."),
        impact=("An unthrottled endpoint is available to credential-stuffing and "
                "enumeration at whatever rate the infrastructure permits."),
        limitations=("This burst is tiny and the limiter may be counting somewhere this "
                     "run cannot see — at the edge, per account, or over a longer window. "
                     "Absence of a 429 here is a coverage gap, not evidence of an "
                     "unthrottled service. The burst was deliberately kept small, and "
                     "raising the volume to make the point is not a step this tool takes."),
        remediation=("Confirm the limiter's configuration with the asset owner rather than "
                     "raising the request volume."),
        scope_summary=scope_summary)]


def schema_consistency(records, cid="E-SCHEMA", scope_summary=None):
    """Two responses FROM THE SAME ENDPOINT with a different JSON shape."""
    usable = [r for r in records if (r.get("response") or {}).get("body_text")]
    out = []
    for (method, url), group in _by_endpoint(usable).items():
        if len(group) < 2:
            continue
        base = group[0]
        for other in group[1:]:
            result = diffmod.compare_records(base, other)
            structural = result["json_structure"]
            if not structural.get("parsed") or not structural.get("count"):
                continue
            out.append(_mk(
                other, f"{cid}-SHAPE-{_slug(url)[:24]}",
                "JSON response shape differs between two calls to the same endpoint",
                severity="informational", confidence="medium", status="OBSERVED",
                expected="An endpoint's response shape is stable for equivalent requests.",
                observed=(f"{method} {url}: against {base.get('id')}, "
                          f"+{len(structural['added_keys'])} keys, "
                          f"-{len(structural['removed_keys'])} keys, "
                          f"~{len(structural['changed_types'])} type changes."),
                impact=("A shape that varies with input is a hint that error paths, "
                        "alternative branches and partial objects are reachable."),
                limitations=("Shapes legitimately vary: a paginated response may omit a "
                             "key, and an error path may return a different object on "
                             "purpose. This is a signal to read the endpoint's contract, "
                             "not a finding."),
                remediation="Document the intended shape, and ensure error responses are "
                            "distinguishable from empty successes.",
                scope_summary=scope_summary))
    return out


def predictable_identifier(record, cid="E-ID", scope_summary=None):
    """A sequential identifier in the URL. An observation, never a finding."""
    from urllib.parse import urlsplit
    path = urlsplit(record.get("url") or "").path or ""
    segments = [s for s in path.split("/") if s]
    for segment in reversed(segments):
        if re.fullmatch(r"\d{1,12}", segment):
            return [_mk(
                record, f"{cid}-SEQUENTIAL",
                f"Sequential numeric identifier in the path: {segment}",
                severity="informational", confidence="high", status="OBSERVED",
                expected=("Object references that are not intended to be enumerable are "
                          "not sequential integers."),
                observed=f"Path segment {segment!r} is a small integer.",
                impact=("Enumerable identifiers make object-level authorization the only "
                        "barrier preventing one user from reading another's object, and "
                        "make an unauthorized read trivially reachable."),
                limitations=("Sequential identifiers are entirely normal and are not a "
                             "defect. This record flags a place where object-level "
                             "authorization deserves a deliberate test with a second "
                             "authorized identity — which this check does not perform."),
                remediation=("Ensure object-level authorization is enforced per request. "
                             "Random identifiers reduce discoverability but are not a "
                             "substitute for the check."),
                scope_summary=scope_summary)]
    return []


def authorization_boundary(record_a, record_b, identity_a, identity_b,
                           cid="E-AUTHZ", scope_summary=None):
    """Compare the same object fetched as two authorized identities.

    This is the only check here that can say something meaningful about access
    control, and it is deliberately narrow: both identities must be supplied by
    the operator, both requests must already have been captured, and the result
    is a `POTENTIAL` record that names the difference and states what would have
    to be true for it to be a defect.

    The workbench does not create identities, does not obtain credentials, and
    does not attempt to reach an object it was not already able to fetch.
    """
    if not identity_a or not identity_b:
        return []
    result = diffmod.compare_records(record_a, record_b)
    status_a = result["status"]["from"]
    status_b = result["status"]["to"]
    same_body = result["body"]["normalised_equal"]
    both_ok = (isinstance(status_a, int) and isinstance(status_b, int)
               and status_a < 300 and status_b < 300)
    if not both_ok:
        return []
    if same_body:
        return []
    return [_mk(
        record_b, f"{cid}-DIFFERS",
        f"Same object returned differently to two authorized identities "
        f"({identity_a} vs {identity_b})",
        severity="low", confidence="low", status="POTENTIAL",
        expected=("If both identities are entitled to the object, the response may "
                  "still differ for fields that are per-identity."),
        observed=(f"Status {status_a} for {identity_a}, {status_b} for {identity_b}; "
                  f"{result['difference_count']} section(s) differ; bodies are not "
                  f"identical."),
        impact=("If the second identity is not entitled to this object, a 2xx response "
                "with the object's content is an object-level authorization failure. "
                "If it is entitled, the difference is expected and this record is "
                "closed."),
        limitations=("This comparison cannot tell entitlement from lack of it: only "
                     "the engagement's authorization record says whether identity B "
                     "should see this object. Per-identity fields (a display name, a "
                     "flag, a timestamp) also differ legitimately. A human must read "
                     "the difference and decide; nothing here may be reported as a "
                     "finding until that has happened."),
        remediation=("Enforce object-level authorization on every request that takes "
                     "an object reference, and test it with a second identity as part "
                     "of the release gate."),
        scope_summary=scope_summary,
        notes=f"identity_a={identity_a} identity_b={identity_b}")]


def upload_validation_observation(record, cid="E-UPLOAD", scope_summary=None):
    """A recorded multipart upload whose response indicates acceptance."""
    content_type = ""
    for name, value in ((record.get("request_headers") or {}).items()):
        if name.lower() == "content-type":
            content_type = value
    if "multipart/form-data" not in content_type:
        return []
    response = (record.get("response") or {})
    status = response.get("status")
    if not isinstance(status, int) or status >= 300:
        return []
    return [_mk(
        record, f"{cid}-ACCEPTED",
        "Multipart upload accepted by the endpoint",
        severity="informational", confidence="medium", status="OBSERVED",
        expected="Uploads are validated by content, size and destination, not by the "
                 "filename or the declared part type alone.",
        observed=f"Status {status} for a multipart request "
                 f"({response.get('content_type') or 'no content type'}).",
        impact=("An upload path that validates only the declared name or type can be made "
                "to store content the application later serves. Whether it can depends on "
                "where the stored file is written and how it is served."),
        limitations=("This record shows that a multipart request was accepted. It does not "
                     "show that the stored file is reachable, that its type was "
                     "mis-declared, or that any validation is missing. Testing those "
                     "requires deliberately crafted uploads, which the workbench does not "
                     "generate — a file written to disk is not something to automate "
                     "without a person deciding it is in scope."),
        remediation=("Validate uploads by content sniffing and by an allowlist of types, "
                     "store outside the web root, and serve with a fixed content type and "
                     "Content-Disposition: attachment."),
        scope_summary=scope_summary)]


def consolidate(records, max_examples=8):
    """Merge identical observations into one record that lists where they were seen.

    Thirteen responses produced thirteen identical "header absent" records, which
    buries the two records that matter and inflates a bundle's size until nobody
    reads it. Observations of the same condition in the same status are merged;
    `POTENTIAL` records are never merged, because each one is attached to a
    specific response that a human has to go and look at.
    """
    merged, order = {}, []
    for record in records:
        if record.status != "OBSERVED":
            order.append(record)
            continue
        key = (record.id.split("-")[0] + "-" + record.id.split("-")[1], record.title)
        record.affected = [record.target]
        if key not in merged:
            merged[key] = record
            order.append(record)
        else:
            keep = merged[key]
            keep.affected.append(record.target)
            keep.as_dict()          # ensure payload is materialised before editing
            keep.observed = _merge_observed(keep, len(keep.affected), max_examples)
    for record in order:
        if getattr(record, "affected", None) and len(record.affected) > 1:
            record.observed = _merge_observed(record, len(record.affected), max_examples)
            record.notes = ((record.notes + " | ").strip(" |") +
                            f"observed on {len(record.affected)} response(s)")
    return order


def _merge_observed(record, count, max_examples):
    base = record.observed.split(" Also observed on ")[0]
    examples = ", ".join(sorted(set(record.affected))[:max_examples])
    more = "" if count <= max_examples else f" (+{count - max_examples} more)"
    return (f"{base} Also observed on {count - 1} other response(s) in this run: "
            f"{examples}{more}")


def _slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(text)).strip("-").lower()[:40] or "item"


# The registry. Order is the order records appear in a bundle, which keeps a
# report's numbering stable across runs.
SINGLE_CHECKS = (
    ("headers", security_headers),
    ("cookies", cookie_flags),
    ("cors", cors_configuration),
    ("cache", cache_of_authenticated_response),
    ("content-type", content_type_handling),
    ("redirects", redirect_behavior),
    ("tls", tls_indicators),
    ("errors", error_disclosure),
    ("reflection", reflected_input),
    ("open-redirect", open_redirect_indicator),
    ("methods", method_handling),
    ("identifiers", predictable_identifier),
    ("uploads", upload_validation_observation),
)

GROUP_CHECKS = (
    ("rate-limit", rate_limit_behavior),
    ("schema", schema_consistency),
)

CHECK_NAMES = tuple(name for name, _ in SINGLE_CHECKS) + \
    tuple(name for name, _ in GROUP_CHECKS) + ("authorization",)


def run_checks(records, *, only=None, scope_summary=None, bundle=None, identities=None,
               group_window=20):
    """Apply the selected checks to a set of stored records.

    Returns the records produced, and adds them to `bundle` when one is given.
    `identities` enables the authorization-boundary comparison and is a tuple of
    (label_a, label_b, id_a, id_b); without it that check does not run at all
    rather than running in a degraded form.
    """
    # `only=None` means every check. An empty list means none: a caller who
    # computed a selection and got nothing back must not receive every check
    # instead, which is the failure mode where a scoped run quietly becomes a
    # full one.
    selected = set(CHECK_NAMES) if only is None else set(only)
    produced = []
    for name, function in SINGLE_CHECKS:
        if name not in selected:
            continue
        for record in records:
            for item in function(record, scope_summary=scope_summary):
                produced.append(item)
    for name, function in GROUP_CHECKS:
        if name not in selected:
            continue
        window = records[:group_window] if group_window else records
        for item in function(window, scope_summary=scope_summary):
            produced.append(item)
    if "authorization" in selected and identities:
        label_a, label_b, id_a, id_b = identities
        by_id = {r.get("id"): r for r in records}
        if id_a in by_id and id_b in by_id:
            produced.extend(authorization_boundary(by_id[id_a], by_id[id_b],
                                                   label_a, label_b,
                                                   scope_summary=scope_summary))
    produced = consolidate(produced)
    # Ids must be unique inside a bundle, so duplicates from two records with the
    # same condition are merged rather than overwritten on write.
    seen = {}
    for item in produced:
        if item.id in seen:
            item.id = f"{item.id}-{len(seen) + 1}"
        seen[item.id] = item
        if bundle is not None:
            bundle.add(item)
    return produced
