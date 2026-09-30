"""Tests for discovery under an allowlist.

The behavioural tests here are mostly about what discovery does *not* fetch:

* a link to another host is recorded and never requested;
* a path the scope excludes is refused by the guard even though the tool found it
  itself in the target's own sitemap, and the target never sees the request;
* the page cap, the depth cap and the budget each stop the crawl, and the run
  says what it left behind;
* a form is read, never submitted.

The parsing tests cover the documents a crawl reads (`robots.txt`, sitemaps,
forms, an API description, a script) because those decide what the crawl will
believe about the target.
"""

from __future__ import annotations

import json

from workbench import discover
from workbench import history as hist
from workbench import http_client as hc
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains

HOST = "127.0.0.1"


def _guard(server, **overrides):
    data = fixtures.scope_data(**overrides)
    return sc.ScopeGuard(sc.Scope(data), resolve=lambda host: [HOST])


def _run(server, path="/", **kw):
    guard = _guard(server, **kw.pop("scope_overrides", {}))
    h = hist.History()
    discovery = discover.discover(guard, server.url(path), history=h, **kw)
    return discovery, h, guard


# ------------------------------------------------------------------ references
def test_references_keep_the_attribute_that_linked_them():
    html = ('<a href="/a">a</a><img src="/b.png"><form action="/c"></form>'
            '<meta content="/d">')
    equal(discover.references(html),
          [("href", "/a"), ("src", "/b.png"), ("action", "/c"), ("content", "/d")])


def test_references_skip_fragments_and_duplicates():
    html = '<a href="#top">x</a><a href="/a">1</a><a href="/a">2</a>'
    equal(discover.references(html), [("href", "/a")])


def test_absolute_ignores_references_that_are_not_addresses():
    equal(discover.absolute("http://h/p", "javascript:void(0)"), "")
    equal(discover.absolute("http://h/p", "mailto:a@b"), "")
    equal(discover.absolute("http://h/p", "data:text/plain,x"), "")
    equal(discover.absolute("http://h/dir/page", "next"), "http://h/dir/next")
    equal(discover.absolute("http://h/dir/page", "https://other/x"), "https://other/x")


def test_within_root_keeps_a_crawl_in_its_tree():
    equal(discover.within_root("http://h/app/a", "http://h/app/"), True)
    equal(discover.within_root("http://h/other", "http://h/app/"), False)
    equal(discover.within_root("http://h/app/a", "http://h/"), True)
    equal(discover.within_root("https://h/app/a", "http://h/app/"), False)


def test_classification_prefers_the_status_over_the_declared_type():
    """A 404 served as text/plain is not a document."""
    equal(discover.classify("http://h/x", "text/plain", 404), "missing")
    equal(discover.classify("http://h/x", "text/plain", 410), "missing")
    equal(discover.classify("http://h/x", "text/plain", 500), "error")
    equal(discover.classify("http://h/x", "text/plain", 200), "document")
    equal(discover.classify("http://h/x", "application/json", 200), "data")
    equal(discover.classify("http://h/logo.png", "", 200), "asset")
    equal(discover.classify("http://h/manual.pdf", "", 200), "resource")


# ------------------------------------------------------------------- documents
def test_robots_parser_reports_the_policy_and_the_sitemaps():
    text = ("User-agent: *\n"
            "Disallow: /private\n"
            "Allow: /private/open\n"
            "Sitemap: http://h/sitemap.xml\n"
            "# a comment\n")
    parsed = discover.parse_robots(text)
    equal(parsed["disallow"], ["/private"])
    equal(parsed["allow"], ["/private/open"])
    equal(parsed["sitemaps"], ["http://h/sitemap.xml"])
    equal(parsed["user_agents"], ["*"])
    equal(discover.parse_robots(""), {"sitemaps": [], "disallow": [], "allow": [],
                                      "user_agents": []})


def test_sitemap_parser_returns_locations():
    xml = ("<urlset><url><loc>http://h/a</loc></url>"
           "<url><loc> http://h/b </loc></url></urlset>")
    equal(discover.parse_sitemap(xml), ["http://h/a", "http://h/b"])


def test_form_parser_describes_fields_without_submitting_anything():
    html = ('<form action="/login" method="post">'
            '<input type="text" name="user" required>'
            '<input type="password" name="pass">'
            '<input type="hidden" name="csrf" value="x">'
            '<input type="file" name="upload">'
            '<select name="role"><option>a</option></select>'
            '<textarea name="notes"></textarea></form>')
    forms = discover.parse_forms(html, "http://h/dir/page")
    equal(len(forms), 1)
    equal(forms[0]["action"], "http://h/login")
    equal(forms[0]["method"], "POST")
    equal([f["name"] for f in forms[0]["fields"]],
          ["user", "pass", "csrf", "upload", "role", "notes"])
    equal(forms[0]["has_file_field"], True)
    equal(forms[0]["has_password_field"], True)
    equal(forms[0]["fields"][0]["required"], True)
    equal(forms[0]["fields"][2]["value_present"], True)


def test_form_parser_ignores_unlabelled_inputs():
    forms = discover.parse_forms('<form><input type="text"></form>', "http://h/")
    equal(forms[0]["fields"], [])


def test_openapi_parser_lists_operations_and_marks_the_write_ones():
    document = json.loads("""{
      "openapi": "3.0.0",
      "servers": [{"url": "https://api.example.test"}],
      "paths": {
        "/items/{id}": {
          "get": {"parameters": [{"name": "id", "in": "path", "required": true}]},
          "delete": {"operationId": "removeItem", "security": [{"oauth": []}]}
        },
        "/items": {"post": {"requestBody": {"content": {"application/json": {}}}}}
      }
    }""")
    parsed = discover.parse_openapi(document)
    equal(parsed["valid"], True)
    equal(parsed["version"], "openapi 3.0.0")
    equal(len(parsed["operations"]), 3)
    by_method = {o["method"]: o for o in parsed["operations"]}
    equal(by_method["GET"]["parameters"][0]["name"], "id")
    equal(by_method["DELETE"]["declares_write"], True)
    equal(by_method["DELETE"]["declares_auth"], True)
    equal(by_method["POST"]["parameters"][0]["in"], "body")
    equal(by_method["GET"]["declares_write"], False)


def test_openapi_parser_reports_a_document_it_cannot_read():
    parsed = discover.parse_openapi({"paths": {}})
    equal(parsed["valid"], False)
    contains(parsed["reason"], "openapi")
    equal(discover.parse_openapi("not a document")["valid"], False)


def test_js_reader_collects_paths_and_ignores_absolute_urls():
    script = ("const a = '/api/items/1'; const b = \"https://cdn.example/lib.js\";"
              " const c = '//host/proto-relative'; const d = '/graphql';"
              " const e = '/api/items/1';")
    found = discover.parse_js_references(script)
    contains(found, "/api/items/1")
    contains(found, "/graphql")
    equal([f for f in found if "http" in f], [])
    equal(found.count("/api/items/1"), 1)


def test_graphql_is_reported_only_when_the_target_referenced_it():
    equal(discover.probe_graphql(["/graphql", "/api/graphql", "/about", "/search"]),
          ["/api/graphql", "/graphql"])
    equal(discover.probe_graphql(["/about", "/contact"]), [])


# ------------------------------------------------------------------- end to end
def test_a_run_finds_the_documents_the_target_publishes():
    with fixtures.FixtureServer() as srv:
        discovery, h, _guard_obj = _run(srv, max_pages=20, max_depth=3)
        kinds = discovery.summary()["by_kind"]
        equal(kinds.get("robots"), 1)
        equal(kinds.get("sitemap"), 1)
        equal(kinds.get("api-description"), 1)
        urls = [f.url for f in discovery.findings]
        check(any(url.endswith("/openapi.json") for url in urls), "the API description was found")
        equal(len(h.entries), discovery.pages_fetched)


def test_the_api_description_is_read_and_its_operations_are_not_called():
    """Reading a description is not calling what it describes.

    The fixture's script also references `/api/items/1`, so this runs with the
    script reader off: any request to that path would then have come from the
    document, which is the thing under test.
    """
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3, read_scripts=False)
        described = [f for f in discovery.findings if f.kind == "api-description"]
        equal(len(described), 1)
        operations = described[0].detail["operations"]
        check(len(operations) >= 2, "operations are listed from the document")
        contains(described[0].note, "none of them was called")
        equal([h["path"] for h in srv.hits if h["path"].startswith("/api/items/")], [],
              "an operation named in a document is not requested")


def test_a_script_reference_is_what_fetches_an_api_path():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        script_refs = [f for f in discovery.findings
                       if "/api/items/1" in f.url and "written in the script" in f.source]
        equal(len(script_refs), 1)
        equal(script_refs[0].status, 200)


def test_a_link_to_another_host_is_recorded_and_never_requested():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        external = [f for f in discovery.findings if f.kind == "external"]
        equal(len(external), 1)
        equal(external[0].in_scope, False)
        equal(external[0].url, "https://fixture.invalid/external")
        equal(len(discovery.refused), 2)
        check(any("different host" in r["reason"] for r in discovery.refused), "reason recorded")


def test_a_path_the_scope_excludes_is_refused_and_never_reaches_the_target():
    """The exclusion comes from the target's own sitemap, and it still holds."""
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        refused = [r for r in discovery.refused if "/private" in r["url"]]
        equal(len(refused), 1)
        contains(refused[0]["reason"], "ScopeError")
        equal([h["path"] for h in srv.hits if "/private" in h["path"]], [])


def test_the_page_cap_stops_the_crawl_and_says_what_it_left():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=3, max_depth=3)
        check(discovery.pages_fetched <= 3, "the page cap is a hard cap")
        summary = discovery.summary()
        equal(summary["max_pages"], 3)
        check(summary["not_followed_by_cap"] > 0,
              "what the cap stopped must be reported, not omitted")


def test_the_depth_cap_stops_the_crawl():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=40, max_depth=0)
        equal(discovery.summary()["max_depth"], 0)
        crawled = [f for f in discovery.findings if f.depth and f.depth > 0 and f.status]
        equal(crawled, [], "depth 0 fetches the root and the published documents only")


def test_a_small_budget_leaves_the_rest_of_the_frontier_reported():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        h = hist.History()
        discovery = discover.discover(guard, srv.url("/"), history=h, max_pages=30,
                                      max_depth=3, budget=4)
        check(discovery.requests_used <= 4,
              f"the run made {discovery.requests_used} requests against a budget of 4")
        check(len(h.entries) <= 4, "the budget bounds what was sent")
        check(discovery.not_followed, "the frontier that was not reached is listed")


def test_cancellation_stops_the_run_and_keeps_what_it_had():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        discovery = discover.discover(guard, srv.url("/"), max_pages=30, max_depth=3,
                                      cancel_check=lambda: True)
        equal(discovery.cancelled, True)
        equal(discovery.pages_fetched, 1, "the request the operator asked for still ran")


def test_assets_can_be_left_out_and_are_then_reported_as_unfollowed():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3, include_assets=False)
        equal(discovery.summary()["by_kind"].get("resource", 0), 0)
        equal([h["path"] for h in srv.hits if h["path"] == "/file.pdf"], [],
              "a skipped asset must not be requested")
        check(any(url.endswith("/file.pdf") for url in discovery.not_followed),
              "a skipped asset is listed rather than silently dropped")


def test_a_form_is_read_and_never_submitted():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        forms = discovery.by_kind("form")
        equal(len(forms), 1)
        equal(forms[0].method, "POST")
        contains(forms[0].note, "read, not submitted")
        equal([h["method"] for h in srv.hits if h["method"] != "GET"], [])


def test_every_finding_says_where_it_came_from():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        for finding in discovery.findings:
            check(finding.source, f"{finding.url} has no recorded origin")
        linked = [f for f in discovery.findings if "attribute on" in f.source]
        check(linked, "references carry the attribute that linked them")


def test_a_script_reference_is_read_and_a_file_shaped_one_is_not_fetched():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        script_refs = [f for f in discovery.findings if f.kind == "script-reference"]
        equal(script_refs, [], "the fixture's script names endpoints, not files")
        fetched = [f for f in discovery.findings if "written in the script" in f.source]
        check(fetched, "endpoint-shaped references are fetched")
        equal(discover.graphql_references(discovery),
              [f.url for f in fetched if f.url.endswith("/graphql")])


def test_the_summary_and_report_state_what_discovery_cannot_conclude():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=20, max_depth=3)
        contains(discovery.summary()["note"], "does not establish that anything else is absent")
        report = discovery.report_lines()
        contains(report, "does not exist")
        contains(report, "pages fetched")
        contains(report, "out of scope")


def test_a_base_url_that_cannot_be_fetched_returns_an_empty_run_not_an_exception():
    with fixtures.FixtureServer() as srv:
        guard = _guard(srv)
        discovery = discover.discover(guard, "http://not-in-scope.invalid/", max_pages=5)
        equal(discovery.findings, [])
        equal(discovery.pages_fetched, 0)
        equal(len(discovery.refused), 1)
        contains(discovery.refused[0]["reason"], "ScopeError")


def test_the_same_url_is_never_fetched_twice_in_one_run():
    with fixtures.FixtureServer() as srv:
        discovery, _h, _g = _run(srv, max_pages=30, max_depth=3)
        paths = [h["path"] for h in srv.hits]
        equal(len(paths), len(set(paths)), f"a URL was fetched twice: {sorted(paths)}")
        equal(discovery.pages_fetched, len(paths))
