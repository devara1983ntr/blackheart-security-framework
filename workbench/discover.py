"""Discovery under an allowlist, a budget and a page cap.

What this does
--------------
Finds things that are already public about a target: `robots.txt`, sitemaps,
the links and forms on a page, an OpenAPI or Swagger document the target
publishes, a GraphQL endpoint that the target itself advertises, references in
JavaScript files, and static assets. Then it records where each one came from.

What it will not do
-------------------
Crawl outside the host that was authorised, follow a link merely because it was
linked, or discover anything by trying names. The list of candidate paths is
empty: there is no wordlist, no extension sweep, no `admin`, no `.git`, no
backup-file guessing. A discovery tool with a wordlist is a content scanner, and
a content scanner on a system you are authorised to test is still a scanner whose
results nobody can bound.

The three limits that matter
----------------------------
* **Scope, per request.** Every fetch goes through `ScopeGuard`, including the
  fetches the crawler performs on its own account. Discovery is where a tool
  most easily wanders: a page links to a CDN, a sitemap lists a third-party host,
  a redirect points at a login portal. Each of those is recorded as *out of
  scope, not followed* rather than fetched.
* **Depth and pages.** Bounded by the caller and by the scope file. A run
  reports the frontier it did not exhaust, because a crawl that stopped early
  and does not say so is worse than one that never started.
* **Bytes.** Response bodies are capped during the read by the HTTP client, so a
  200 MB page cannot fill memory or the evidence directory.

Everything found is described by where it came from, and everything the target
declined to serve is described as unavailable with the status that said so.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse

from . import http_client as hc

# The paths this framework will request on its own initiative, and why each is
# justified: each is a document a site publishes *for* automated clients. Adding
# a path here is adding a request the operator did not individually write, so the
# bar is "the target intends this to be fetched".
WELL_KNOWN_PATHS = (
    ("/robots.txt", "the crawler-policy file, published for automated clients"),
    ("/sitemap.xml", "the sitemap a site publishes for crawlers"),
    ("/sitemap_index.xml", "the sitemap index, for sites that split theirs"),
    ("/openapi.json", "an OpenAPI document at the conventional location"),
    ("/swagger.json", "a Swagger document at the conventional location"),
    ("/openapi.yaml", "an OpenAPI document in YAML"),
    ("/api/openapi.json", "an OpenAPI document under an api prefix"),
    ("/api-docs", "a documentation endpoint some frameworks publish"),
    ("/.well-known/security.txt", "the security contact file, published by design"),
)

# A GraphQL endpoint is only reported when the site's own page or script
# references it. Probing conventional GraphQL paths is not discovery, it is
# guessing at an endpoint and reading whether it happened to exist.
GRAPHQL_MARKERS = ("/graphql", "/api/graphql", "/query", "/v1/graphql")

ASSET_EXTENSIONS = (".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp",
                    ".woff", ".woff2", ".ttf", ".pdf", ".zip", ".tar.gz", ".csv",
                    ".json", ".xml", ".txt", ".map")

# Files whose contents are worth fetching for reference extraction. A JavaScript
# file is text; a font is not, and reading it as if it were produces noise.
TEXTUAL_EXTENSIONS = (".js", ".json", ".xml", ".txt", ".css", ".yml", ".yaml", ".md")

LINK_PATTERN = re.compile(
    r"""\b(href|src|action|data-url|content)\s*=\s*["']([^"'#][^"']*)["']""", re.I)
SCRIPT_SRC_PATTERN = re.compile(r"""<script[^>]+src\s*=\s*["']([^"']+)["']""", re.I)
FORM_PATTERN = re.compile(r"<form\b[^>]*>(.*?)</form>", re.I | re.S)
INPUT_PATTERN = re.compile(r"""<(?:input|select|textarea)\b[^>]*>""", re.I)
ATTR_PATTERN = re.compile(r"""(\w+)\s*=\s*["']([^"']*)["']""")
JS_PATH_PATTERN = re.compile(r"""["'](/[A-Za-z0-9_\-./{}$:]{2,120})["']""")
OPENAPI_VERSION_KEYS = ("openapi", "swagger")


class DiscoveryError(Exception):
    """Raised for a discovery request that cannot be honoured as asked."""


def _may_fetch(guard, discovery):
    """Whether this run may make another request.

    Both limits are checked: the run's own budget, and the scope file's
    lifetime cap that the guard enforces. The budget used to be recorded and
    never enforced — a parameter that reads as a limit and does nothing is
    worse than no parameter, because the caller believes the run was bounded.
    """
    if discovery.requests_used >= discovery.budget:
        return False
    if guard.requests_made >= guard.scope.max_requests:
        return False
    return True


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def references(html):
    """`(attribute, value)` for every reference on a page.

    The attribute is kept because it is the provenance: a `src` is a resource the
    page loads, an `action` is where a form submits, an `href` is somewhere a
    reader can go. A URL found on a page without that context is a URL nobody can
    account for.
    """
    out = []
    for match in LINK_PATTERN.finditer(html or ""):
        attribute, value = match.group(1).lower(), match.group(2)
        if value and (attribute, value) not in out:
            out.append((attribute, value))
    return out


def absolute(base, candidate):
    """Resolve a reference against the page it was found on."""
    if not candidate:
        return ""
    candidate = candidate.strip()
    if candidate.startswith(("javascript:", "mailto:", "tel:", "data:", "#")):
        return ""
    try:
        return urllib.parse.urljoin(base, candidate)
    except ValueError:
        return ""


def same_host(url, host):
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower() == (host or "").lower()
    except ValueError:
        return False


def within_root(url, base_url):
    """True when `url` is under the base URL's path, so a crawl stays in its tree."""
    base = urllib.parse.urlsplit(base_url)
    target = urllib.parse.urlsplit(url)
    if (target.hostname or "").lower() != (base.hostname or "").lower():
        return False
    if (target.port or (443 if target.scheme == "https" else 80)) != \
            (base.port or (443 if base.scheme == "https" else 80)):
        return False
    root = base.path if base.path.endswith("/") else base.path.rsplit("/", 1)[0] + "/"
    if root in ("", "/"):
        return True
    return target.path.startswith(root.rstrip("/")) or target.path == base.path


def classify(url, content_type="", status=None):
    """What a discovered URL is, from its status, its path and its declared type.

    Status is checked first: a 404 whose body is `text/plain` was being
    classified as `document`, which made a URL the target declined look like a
    page the crawl had reached.
    """
    path = urllib.parse.urlsplit(url).path.lower()
    declared = (content_type or "").split(";")[0].strip().lower()
    if isinstance(status, int) and status >= 400:
        return "missing" if status in (404, 410) else "error"
    if declared:
        if "json" in declared:
            return "data"
        if "xml" in declared:
            return "data"
        if declared.startswith("text/") or "javascript" in declared:
            return "document"
        if declared.startswith("image/"):
            return "asset"
        if declared in ("application/pdf", "application/zip", "application/gzip"):
            return "resource"
        if declared == "application/octet-stream":
            return "resource"
    for extension in ASSET_EXTENSIONS:
        if path.endswith(extension):
            return "resource" if extension in (".pdf", ".zip", ".tar.gz") else "asset"
    return "page"


def parse_robots(text):
    """Sitemaps declared by robots.txt, plus the declared crawl policy.

    The `Disallow` lines are reported, not obeyed silently: a crawl that avoids
    a path and does not say why leaves a reader unable to tell a policy from an
    omission.
    """
    sitemaps, disallow, allow, agents = [], [], [], []
    for line in (text or "").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "sitemap" and value:
            sitemaps.append(value)
        elif key == "disallow" and value:
            disallow.append(value)
        elif key == "allow" and value:
            allow.append(value)
        elif key == "user-agent" and value:
            agents.append(value)
    return {"sitemaps": sitemaps, "disallow": disallow, "allow": allow,
            "user_agents": agents}


def parse_sitemap(text):
    """Locations from a sitemap or sitemap index."""
    return [match for match in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text or "", re.I)]


def parse_forms(html, base_url):
    """Forms on a page, with their fields and method.

    A form is a description of a request the site expects. Reading it is how the
    tool knows an endpoint exists without sending anything to it.
    """
    forms = []
    for index, match in enumerate(FORM_PATTERN.finditer(html or "")):
        block = match.group(0)
        attributes = dict((k.lower(), v) for k, v in ATTR_PATTERN.findall(block))
        fields = []
        for tag in INPUT_PATTERN.findall(block):
            attrs = dict((k.lower(), v) for k, v in ATTR_PATTERN.findall(tag))
            name = attrs.get("name")
            if not name:
                continue
            element = re.match(r"<([a-z]+)", tag.strip(), re.I)
            element = element.group(1).lower() if element else "input"
            fields.append({
                "name": name,
                "element": element,
                "type": attrs.get("type", "text" if element == "input" else element),
                "required": "required" in tag.lower(),
                "value_present": bool(attrs.get("value")),
            })
        forms.append({
            "index": index,
            "action": absolute(base_url, attributes.get("action", "")) or base_url,
            "method": (attributes.get("method") or "GET").upper(),
            "fields": fields,
            "has_file_field": any(f["type"] == "file" for f in fields),
            "has_password_field": any(f["type"] == "password" for f in fields),
        })
    return forms


def parse_openapi(document):
    """The operations an OpenAPI or Swagger document declares."""
    if not isinstance(document, dict):
        return {"valid": False, "reason": "not a JSON object", "operations": [],
                "servers": [], "version": None}
    version = None
    for key in OPENAPI_VERSION_KEYS:
        if key in document:
            version = f"{key} {document[key]}"
            break
    operations = []
    for path, item in (document.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method.lower() not in ("get", "head", "options", "post", "put",
                                      "patch", "delete", "trace"):
                continue
            if not isinstance(operation, dict):
                continue
            parameters = []
            for parameter in list(operation.get("parameters") or []) + \
                    list(item.get("parameters") or []):
                if isinstance(parameter, dict) and parameter.get("name"):
                    parameters.append({"name": parameter["name"],
                                       "in": parameter.get("in"),
                                       "required": bool(parameter.get("required"))})
            body = operation.get("requestBody") or {}
            if isinstance(body, dict):
                for media in (body.get("content") or {}):
                    parameters.append({"name": "(request body)", "in": "body",
                                       "required": bool(body.get("required")),
                                       "media_type": media})
            operations.append({
                "path": path,
                "method": method.upper(),
                "operation_id": operation.get("operationId"),
                "parameters": parameters,
                "deprecated": bool(operation.get("deprecated")),
                "declares_write": method.upper() in ("POST", "PUT", "PATCH", "DELETE"),
                "declares_auth": bool(operation.get("security") or document.get("security")),
            })
    servers = []
    for server in document.get("servers") or []:
        if isinstance(server, dict) and server.get("url"):
            servers.append(server["url"])
    return {"valid": version is not None, "version": version, "operations": operations,
            "servers": servers,
            "reason": "" if version is not None else "no openapi/swagger key present"}


def parse_js_references(text):
    """Paths referenced by a script, as candidates to *report*, never to fetch."""
    found = []
    for candidate in JS_PATH_PATTERN.findall(text or ""):
        if candidate.startswith("//") or "://" in candidate:
            continue
        if candidate.count("/") > 6 or len(candidate) < 3:
            continue
        if candidate not in found:
            found.append(candidate)
    return found[:200]


def probe_graphql(candidates):
    """GraphQL endpoints the target itself referenced.

    Returns the references that look like GraphQL. Nothing is requested: an
    introspection query against a guess is an active request the operator did
    not ask for, and `graphql` appearing in a path is evidence only.
    """
    out = []
    for candidate in candidates:
        path = urllib.parse.urlsplit(candidate).path.lower()
        if any(path.endswith(marker) or marker in path for marker in GRAPHQL_MARKERS):
            out.append(candidate)
    return sorted(set(out))


class Finding:
    """One discovered thing, with the provenance that explains how it was found."""

    def __init__(self, url, kind, *, source, status=None, content_type=None,
                 depth=None, method="GET", detail=None, in_scope=None, note=""):
        self.url = url
        self.kind = kind
        self.source = source
        self.status = status
        self.content_type = content_type
        self.depth = depth
        self.method = method
        self.detail = detail or {}
        self.in_scope = in_scope
        self.note = note

    def as_dict(self):
        return {
            "url": self.url,
            "kind": self.kind,
            "source": self.source,
            "status": self.status,
            "content_type": self.content_type,
            "depth": self.depth,
            "method": self.method,
            "in_scope": self.in_scope,
            "detail": self.detail,
            "note": self.note,
        }


class Discovery:
    """The result of one discovery run: what was found and what was not done."""

    def __init__(self, root, budget, max_pages, max_depth):
        self.root = root
        self.budget = budget
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.started_at = None
        self.finished_at = None
        self.findings = []
        self.pages_fetched = 0
        self.bytes_read = 0
        self.refused = []          # out of scope, described rather than fetched
        self.unavailable = []      # in scope, and the server said no
        self.not_followed = []     # in scope, but depth or page cap stopped it
        self.origin = {}           # url -> where the reference came from
        self.cancelled = False
        self.errors = []
        self.requests_seen_at_start = 0
        self.requests_used = 0

    # -- collection ------------------------------------------------------
    def add(self, finding):
        self.findings.append(finding)
        return finding

    def by_kind(self, kind):
        return [f for f in self.findings if f.kind == kind]

    def summary(self):
        kinds = {}
        for finding in self.findings:
            kinds[finding.kind] = kinds.get(finding.kind, 0) + 1
        return {
            "root": self.root,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "pages_fetched": self.pages_fetched,
            "budget": self.budget,
            "requests_used": self.requests_used,
            "max_pages": self.max_pages,
            "max_depth": self.max_depth,
            "findings": len(self.findings),
            "by_kind": kinds,
            "refused_out_of_scope": len(self.refused),
            "unavailable": len(self.unavailable),
            "not_followed_by_cap": len(self.not_followed),
            "bytes_read": self.bytes_read,
            "cancelled": self.cancelled,
            "errors": len(self.errors),
            "note": ("Discovery lists what the target published. It does not "
                     "establish that anything else is absent: a path that was not "
                     "referenced, not listed and not guessed at was not tested."),
        }

    def report_lines(self):
        summary = self.summary()
        lines = [
            f"Discovery from {summary['root']}",
            f"  pages fetched   : {summary['pages_fetched']} of at most "
            f"{summary['max_pages']} (depth {summary['max_depth']}, "
            f"{summary['requests_used']} of {summary['budget']} requests used)",
            f"  found           : {summary['findings']} {summary['by_kind']}",
            f"  out of scope    : {summary['refused_out_of_scope']} reference(s) not followed",
            f"  unavailable     : {summary['unavailable']} in-scope URL(s) the target declined",
            f"  stopped by caps : {summary['not_followed_by_cap']} reference(s) left in the frontier",
        ]
        if summary["cancelled"]:
            lines.append("  cancelled       : yes — partial results retained")
        lines.append("")
        lines.append("  A crawl reports what it reached. Nothing here says that a "
                     "path it did not reach does not exist.")
        return "\n".join(lines)


def _fetch_text(guard, url, *, tag, history, discovery, max_bytes=None):
    """Fetch one URL, recording whatever happens. Returns `(record, text)`."""
    before = guard.requests_made
    try:
        exchange = hc.request(guard, url, "GET", note=tag, max_bytes=max_bytes)
    except Exception as exc:                                   # ScopeError included
        discovery.refused.append({"url": url, "reason": f"{type(exc).__name__}: {exc}"})
        return None, ""
    finally:
        discovery.requests_used += guard.requests_made - before
    record = exchange.record()
    if history is not None:
        history.add(exchange, tag=tag)
    discovery.pages_fetched += 1
    discovery.bytes_read += len((record.get("response") or {}).get("body_text") or "")
    return record, (record.get("response") or {}).get("body_text") or ""


def discover(guard, base_url, *, history=None, max_pages=None, max_depth=None,
             budget=None, cancel_check=None, include_assets=True,
             well_known=True, read_scripts=True):
    """Run one bounded discovery pass over an authorised base URL.

    Returns a `Discovery`. Nothing raises for an HTTP failure: a 403 on
    `robots.txt` is a finding about the target, and this is a tool for recording
    findings. `ScopeError` is not raised either — a reference outside the scope
    is recorded in `refused`, which is what makes "it did not crawl that host"
    visible in the output rather than an assumption.
    """
    scope = guard.scope
    budget = int(budget if budget is not None else scope.max_requests)
    max_pages = int(max_pages if max_pages is not None else 25)
    max_depth = int(max_depth if max_depth is not None else 2)
    discovery = Discovery(base_url, budget, max_pages, max_depth)
    discovery.started_at = now()
    discovery.requests_seen_at_start = guard.requests_made

    host = urllib.parse.urlsplit(base_url).hostname or ""
    queued = {base_url}
    visited = set()
    frontier = []

    try:
        # -- the request the operator asked for, then the published documents
        root_record, root_text = _fetch_text(guard, base_url, tag="discover:root",
                                             history=history, discovery=discovery)
        visited.add(base_url)
        if root_record is None:
            discovery.finished_at = now()
            return discovery
        root_type = (root_record.get("response") or {}).get("content_type")
        discovery.add(Finding(base_url, classify(base_url, root_type,
                                                 (root_record.get("response") or {}).get("status")),
                              source="the URL you asked for",
                              status=(root_record.get("response") or {}).get("status"),
                              content_type=root_type, depth=0, in_scope=True))

        if well_known:
            known = _well_known(guard, base_url, history=history, discovery=discovery,
                                visited=visited, cancel_check=cancel_check)
            for finding, document in known:
                discovery.add(finding)
                if document and finding.kind == "sitemap":
                    for location in parse_sitemap(document):
                        _consider(location, source=f"sitemap {finding.url}",
                                  root_url=base_url, host=host, depth=1,
                                  discovery=discovery, visited=visited, queued=queued,
                                  frontier=frontier, max_depth=max_depth,
                                  include_assets=include_assets,
                                  note="listed in the target's own sitemap")
                if document and finding.kind == "robots":
                    robots = parse_robots(document)
                    finding.detail = robots
                    for location in robots["sitemaps"]:
                        _consider(location, source=f"robots.txt of {host}", root_url=base_url,
                                  host=host, depth=1, discovery=discovery, visited=visited,
                                  queued=queued, frontier=frontier, max_depth=max_depth,
                                  include_assets=include_assets,
                                  note="declared in robots.txt")

        # -- the crawl proper
        _walk(guard, root_text, base_url, depth=0, history=history,
              discovery=discovery, visited=visited, queued=queued, frontier=frontier,
              host=host, max_depth=max_depth, max_pages=max_pages,
              include_assets=include_assets, read_scripts=read_scripts,
              cancel_check=cancel_check)
    finally:
        discovery.finished_at = now()
    discovery.not_followed.extend(sorted(frontier))
    return discovery


def _well_known(guard, base_url, *, history, discovery, visited, cancel_check):
    """Fetch the documents a site publishes for automated clients."""
    parsed = urllib.parse.urlsplit(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    out = []
    for path, why in WELL_KNOWN_PATHS:
        url = root + path
        if url in visited:
            continue
        if cancel_check is not None and cancel_check():
            discovery.cancelled = True
            break
        if not _may_fetch(guard, discovery) or _would_exceed(discovery, 0):
            discovery.not_followed.append(url)
            break
        visited.add(url)
        record, text = _fetch_text(guard, url, tag=f"discover:{path}", history=history,
                                   discovery=discovery)
        if record is None:
            continue
        response = record.get("response") or {}
        status = response.get("status")
        content_type = response.get("content_type")
        if status == 200 and text:
            kind = "sitemap" if "sitemap" in path else (
                "robots" if "robots" in path else
                "security-txt" if "security.txt" in path else "api-description")
            finding = Finding(url, kind, source=f"the conventional path {path}", status=status,
                              content_type=content_type, depth=0, in_scope=True, note=why)
            if kind == "api-description":
                _read_api_description(text, content_type, url, finding)
            out.append((finding, text if kind in ("sitemap", "robots") else ""))
        else:
            discovery.unavailable.append({
                "url": url, "status": status, "reason": response.get("error") or "not served",
                "note": why,
            })
            out.append((Finding(url, classify(url, content_type, status),
                                source=f"the conventional path {path}", status=status,
                                content_type=content_type, depth=0, in_scope=True,
                                note="not available at this path"), ""))
    return out


def _read_api_description(text, content_type, url, finding):
    """Attach what an API description declares, without calling any of it."""
    document = None
    if "json" in (content_type or "").lower() or text.lstrip().startswith("{"):
        try:
            document = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            document = None
    if document is None:
        finding.detail = {"parsed": False,
                          "reason": ("not JSON: this reader does not parse YAML "
                                     "descriptions, so its operations are not listed")}
        return
    parsed = parse_openapi(document)
    finding.detail = parsed
    finding.note = (f"declares {len(parsed['operations'])} operation(s); "
                    f"none of them was called")


def _walk(guard, html, page_url, *, depth, history, discovery, visited, queued,
          frontier, host, max_depth, max_pages, include_assets, read_scripts,
          cancel_check):
    """Breadth-first over references that stay inside the authorised root."""
    forms = parse_forms(html, page_url)
    for form in forms:
        discovery.add(Finding(form["action"], "form",
                              source=f"a form on {page_url}",
                              method=form["method"], depth=depth,
                              detail=form, in_scope=None,
                              note=("a form describes a request the site expects; "
                                    "it was read, not submitted")))
    _queue_references(html, page_url, depth=depth + 1, guard=guard, discovery=discovery,
                      visited=visited, queued=queued, frontier=frontier, host=host,
                      max_depth=max_depth, include_assets=include_assets)

    while frontier and discovery.pages_fetched < max_pages:
        if cancel_check is not None and cancel_check():
            discovery.cancelled = True
            return
        if not _may_fetch(guard, discovery):
            return
        url = frontier.pop(0)
        if url in visited:
            continue
        visited.add(url)
        record, text = _fetch_text(guard, url, tag="discover:crawl", history=history,
                                   discovery=discovery)
        if record is None:
            continue
        response = record.get("response") or {}
        status, content_type = response.get("status"), response.get("content_type")
        kind = classify(url, content_type, status)
        if status is not None and status >= 400:
            discovery.unavailable.append({"url": url, "status": status,
                                          "reason": response.get("error") or "declined",
                                          "note": "linked from a page but not served"})
            origin = discovery.origin.get(url, {})
            discovery.add(Finding(url, "missing", source=origin.get("source", "linked from a page"),
                                  status=status, content_type=content_type, depth=depth,
                                  in_scope=True, note=origin.get("note", "")))
            continue
        origin = discovery.origin.get(url, {})
        discovery.add(Finding(url, kind, source=origin.get("source", "linked from a page"),
                              status=status, content_type=content_type, depth=depth,
                              in_scope=True, note=origin.get("note", "")))
        if kind == "page" and text:
            for form in parse_forms(text, url):
                discovery.add(Finding(form["action"], "form", source=f"a form on {url}",
                                      method=form["method"], depth=depth + 1,
                                      detail=form, in_scope=None))
            if depth + 1 <= max_depth:
                _queue_references(text, url, depth=depth + 1, guard=guard,
                                  discovery=discovery, visited=visited, queued=queued,
                                  frontier=frontier, host=host, max_depth=max_depth,
                                  include_assets=include_assets)
        if read_scripts and _is_script(url, content_type) and text:
            for reference in parse_js_references(text):
                _consider(absolute(url, reference),
                          source=f"a path written in the script {url}",
                          root_url=discovery.root, host=host, depth=depth + 1,
                          discovery=discovery, visited=visited, queued=queued,
                          frontier=frontier, max_depth=max_depth,
                          include_assets=include_assets, reference_only=True,
                          note=("named inside a script rather than linked from a page: "
                                "fetched with GET when it looks like an endpoint, "
                                "recorded and left alone when it looks like a file"))


def _is_script(url, content_type):
    declared = (content_type or "").split(";")[0].strip().lower()
    return (urllib.parse.urlsplit(url).path.lower().endswith(".js")
            or "javascript" in declared)


def _queue_references(html, page_url, *, depth, guard, discovery, visited, queued,
                      frontier, host, max_depth, include_assets):
    """Consider every reference on a page, with the attribute as its provenance."""
    for attribute, candidate in references(html):
        note = ""
        if attribute == "action":
            note = ("Where a form submits. Fetched with GET, which is not "
                    "necessarily what the form would send.")
        _consider(absolute(page_url, candidate),
                  source=f"the {attribute} attribute on {page_url}",
                  root_url=discovery.root, host=host, depth=depth,
                  discovery=discovery, visited=visited, queued=queued,
                  frontier=frontier, max_depth=max_depth,
                  include_assets=include_assets, note=note)


def _would_exceed(discovery, extra):
    return discovery.pages_fetched + extra >= discovery.max_pages


def _consider(url, *, source, root_url, host, depth, discovery, visited, queued,
              frontier, max_depth, include_assets=True, reference_only=False,
              note=""):
    """Decide what to do with a reference: queue it, or record why not.

    Nothing here is fetched. The decision is recorded either way, because "we
    saw a link to another host and did not follow it" is information a reader of
    the report needs, and a silent skip looks the same as a link that was never
    there.
    """
    if not url:
        return
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        return
    if same_host(url, host) is False:
        discovery.refused.append({
            "url": url, "reason": "a different host than the one in scope",
            "source": source,
            "note": "linked to, not authorised, not fetched",
        })
        discovery.add(Finding(url, "external", source=source, depth=depth, in_scope=False,
                              note="a different host; not fetched"))
        return
    if not within_root(url, root_url):
        discovery.refused.append({"url": url,
                                  "reason": "outside the path the run was started from",
                                  "source": source})
        discovery.add(Finding(url, "outside-root", source=source, depth=depth,
                              in_scope=True, note="outside the start path; not fetched"))
        return
    if reference_only and classify(url) in ("asset", "resource"):
        # A file name inside a script is a reference to something that is served,
        # not an invitation to fetch it. It is recorded, with the script that
        # named it, and left alone.
        discovery.not_followed.append(url)
        discovery.add(Finding(url, "script-reference", source=source, depth=depth,
                              in_scope=True,
                              note="named inside a script; recorded, not fetched"))
        return
    if depth > max_depth:
        discovery.not_followed.append(url)
        return
    if not include_assets and classify(url) in ("asset", "resource"):
        discovery.not_followed.append(url)
        return
    if url in queued or url in visited:
        return
    queued.add(url)
    discovery.origin[url] = {"source": source, "note": note,
                             "reference_only": reference_only}
    frontier.append(url)


def graphql_references(discovery):
    """GraphQL endpoints the target referenced, from everything discovered."""
    candidates = [f.url for f in discovery.findings if f.url]
    return probe_graphql(candidates)
