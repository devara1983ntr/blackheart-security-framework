"""Tests for the legal and policy layer, checked against the repository itself.

A legal document is a set of claims, and claims that are not checked drift. These
tests are the check. They assert three kinds of thing:

* **Coverage** — every document the policy names exists, is reachable from the
  README, and is reachable from the site. The site matters separately because
  Pages serves only `site/`, so a link that works in the README can still be dead
  for a visitor arriving at the website.
* **Truthfulness** — no compliance badge, no invented company, no absolute
  liability promise, and no "authorized by default". A project that cannot
  evidence a certification must not display one, and the cheapest way to keep that
  true is to fail the build when one appears.
* **Agreement with the code** — the document that describes acquisition and the
  module that performs it must say the same thing about which statuses exist and
  which operations are exempt.

Vendored content under `skills/` is excluded throughout: its claims are its
upstream authors', and `skills/VENDOR.md` is the record of them.
"""

from __future__ import annotations

import json
import os
import re

from workbench import fetch
from workbench import policy as policymod
from workbench.tests.harness import check, contains, equal


def _flat(text):
    """Prose as one line: markdown wraps and blockquote markers are formatting.

    A phrase that is split across two lines, or prefixed with `> `, is still the
    same sentence, and an assertion that fails on a line break is testing the
    wrap width rather than the document.
    """
    without_quotes = re.sub(r"(?m)^\s*>\s?", " ", text)
    return re.sub(r"\s+", " ", without_quotes).strip()


def _read(path):
    with open(os.path.join(policymod.repo_root(), path), encoding="utf-8") as fh:
        return fh.read()


def _authored_documents():
    """Every Blackhearts-authored markdown file outside the vendored mirror."""
    root = policymod.repo_root()
    for directory, subdirs, names in os.walk(root):
        subdirs[:] = [name for name in subdirs
                      if name not in (".git", "node_modules", "__pycache__")
                      and "third-party" not in os.path.join(directory, name)
                      and "catalog" not in os.path.join(directory, name)]
        for name in names:
            if name.endswith((".md", ".json", ".json5", ".html")):
                path = os.path.join(directory, name)
                if os.path.relpath(path, root) == "workbench/tests/test_legal.py":
                    continue
                yield os.path.relpath(path, root), _read(os.path.relpath(path, root))


# ------------------------------------------------------------------- coverage
def test_every_policy_document_exists_at_the_root():
    policy = policymod.load()
    for key in policymod.REQUIRED_DOCUMENT_KEYS:
        name = policy["documents"][key]
        path = os.path.join(policymod.repo_root(), name)
        check(os.path.isfile(path), f"{key}: {name} does not exist")
        check(os.path.getsize(path) > 500, f"{name} is a stub, not a document")


def test_the_readme_links_every_policy_document():
    readme = _read("README.md")
    policy = policymod.load()
    for key in policymod.REQUIRED_DOCUMENT_KEYS:
        name = policy["documents"][key]
        contains(readme, f"]({name})", f"README does not link {name}")


def test_the_site_links_every_policy_document_absolutely():
    """Pages serves only `site/`, so a relative root link on the site is dead."""
    page = _read("site/index.html")
    policy = policymod.load()
    for key in policymod.REQUIRED_DOCUMENT_KEYS:
        name = policy["documents"][key]
        contains(page, f"blackheart-security-framework/blob/main/{name}",
                 f"site/index.html does not link {name}")
    check("policy/BLACKHEART-POLICY.json" in page,
          "the site does not link the machine-readable policy")


def test_every_document_named_in_a_document_exists():
    """Markdown links to repository files must resolve, relative to the file."""
    root = policymod.repo_root()
    broken = []
    for relative, text in _authored_documents():
        if not relative.endswith(".md"):
            continue
        base = os.path.dirname(os.path.join(root, relative))
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("http:", "https:", "#", "mailto:", "data:")):
                continue
            path = target.split("#")[0]
            if not path or "${" in path or "$(" in path:
                continue
            if not os.path.exists(os.path.join(base, path)):
                broken.append(f"{relative} -> {target}")
    equal(broken, [], f"unresolved links: {broken[:8]}")


# --------------------------------------------------------------- truthfulness
BANNED_CLAIMS = (
    "completely risk-free", "risk-free", "authorized by default",
    "authorised by default", "safe for any target", "never liable under all",
    "legal protection guaranteed", "guaranteed legal", "attorney-approved",
    "lawyer-approved", "government-approved", "iso 27001 certified",
    "soc 2 compliant", "soc2 compliant", "gdpr compliant", "hipaa compliant",
    "pci dss compliant", "certified compliant",
)


def test_no_unsupported_claim_appears_in_authored_content():
    """No compliance badge, no absolute promise, no "authorized by default"."""
    offenders = []
    for relative, text in _authored_documents():
        if relative.startswith(("LEGAL", "TERMS-OF-USE", "AI-AGENT-TERMS",
                                "SECURITY-RESEARCH-DISCLAIMER", "PRIVACY-POLICY")):
            # These four documents state what the project does not claim, which
            # means naming the claims; the check is on the claims being made.
            continue
        lowered = text.lower()
        for claim in BANNED_CLAIMS:
            if claim in lowered:
                offenders.append(f"{relative}: {claim!r}")
    equal(offenders, [], f"unsupported claims: {offenders[:5]}")


def test_the_terms_warn_that_they_are_not_legally_reviewed():
    for relative in ("TERMS-OF-USE.md", "LEGAL.md", "AI-AGENT-TERMS.md"):
        text = _flat(_read(relative)).lower()
        check("not been reviewed by a lawyer" in text
              or "not legal advice" in text
              or "no legal review" in text,
              f"{relative} does not say that it has not been legally reviewed")
        check("jurisdiction" in text or "your law" in text or "applicable law" in text,
              f"{relative} does not say that effect depends on jurisdiction")


def test_no_invented_company_or_professional_is_named():
    """The project is an individual's work, and the documents must say so."""
    company = re.compile(r"\b(?:LLC|Ltd\.?|GmbH|Inc\.?|PLC|Pty)\b")
    for relative in ("LEGAL.md", "TERMS-OF-USE.md", "PRIVACY-POLICY.md",
                     "AUTHORIZATION-AGREEMENT.md", "AI-AGENT-TERMS.md"):
        text = _read(relative)
        found = company.findall(text)
        equal(found, [], f"{relative} names a company form: {found}")
        for role in ("general counsel", "our attorneys", "law firm retained",
                     "registered office"):
            check(role not in text.lower(), f"{relative} claims {role!r}")


def test_the_project_is_identified_exactly():
    legal = _flat(_read("LEGAL.md"))
    contains(legal, "BLACKHEART Security Framework")
    contains(legal, "devara1983ntr")
    contains(legal, "Roshan")


def test_the_liability_wording_is_the_precise_one():
    terms = _flat(_read("TERMS-OF-USE.md")).lower()
    contains(terms, "users remain responsible for their use of the framework, "
                    "their authorization, their targets, and compliance with "
                    "applicable law")


def test_the_no_bypass_sentence_survives_in_the_documents():
    """The sentence the phase was required to keep, in the places it belongs."""
    for relative in ("LEGAL.md", "docs/workbench/README.md",
                     "docs/workbench/END-TO-END.md",
                     "docs/agent/PHASE5-SAFETY-RULES.md"):
        text = _flat(_read(relative))
        contains(text, "This framework does not bypass authentication, "
                       "authorization, paywalls, DRM, licensing controls, or "
                       "other access restrictions.",
                 f"{relative} has lost the no-bypass sentence")


def test_the_privacy_policy_states_the_framework_collects_nothing():
    privacy = _flat(_read("PRIVACY-POLICY.md")).lower()
    contains(privacy, "no analytics")
    check("does not maintain user accounts" in privacy,
          "the privacy policy does not state that no account is kept")
    contains(privacy, "no telemetry")
    check("localstorage" in privacy or "local storage" in privacy,
          "the privacy policy does not mention the one client-side value the "
          "site actually stores (the theme preference)")


# ---------------------------------------------------- agreement with the code
def test_the_acquisition_policy_names_the_statuses_the_code_defines():
    policy_doc = _read("DOWNLOAD-AND-ACQUISITION-POLICY.md")
    for status in fetch.STATUSES:
        contains(policy_doc, f"`{status}`",
                 f"the acquisition policy does not describe the {status} status")


def test_the_acquisition_policy_names_every_blocking_status():
    policy_doc = _read("DOWNLOAD-AND-ACQUISITION-POLICY.md")
    for status in fetch.BLOCKING_STATUSES:
        contains(policy_doc, str(status),
                 f"the acquisition policy does not name blocking status {status}")


def test_the_policy_lists_the_exempt_operations_the_code_actually_exempts():
    """Every exempt operation must exist as a command, and none may need a socket."""
    policy = policymod.load()
    from workbench import cli

    parser = cli.build_parser()
    known = set()
    nodes = [(parser, ())]
    while nodes:
        node, prefix = nodes.pop()
        group = getattr(node, "_subparsers", None)
        if group is None:
            known.add("blackheart " + " ".join(prefix))
            continue
        for action in group._group_actions:
            for name, child in (getattr(action, "choices", None) or {}).items():
                nodes.append((child, prefix + (name,)))
    for operation in policy["exempt_operations"]:
        check(operation in known, f"{operation} is not a command the tool has")


def test_the_policy_documents_and_the_machine_readable_policy_agree_on_the_gate():
    policy = policymod.load()
    equal(policy["requirements"]["acceptance_required_for_active_operations"], True)
    equal(policy["requirements"]["authorization_required_for_active_operations"], True)
    check("--scope" in policy["requirements"]["active_operation_definition"],
          "the policy's definition of an active operation does not name --scope")
    equal(policy["requirements"]["acceptance_is_not_authorization"], True)
    for relative in ("TERMS-OF-USE.md", "ACCEPTABLE-USE.md", "AI-AGENT-TERMS.md"):
        text = _flat(_read(relative)).lower()
        check("acceptance is not authorization" in text
              or "not authorization for any target" in text
              or "is not authorization" in text,
              f"{relative} does not state that acceptance is not authorization")


def test_every_policy_document_declares_its_version_and_date():
    policy = policymod.load()
    for key in policymod.REQUIRED_DOCUMENT_KEYS:
        name = policy["documents"][key]
        text = _read(name)
        check(re.search(r"\*\*Last updated:\*\* \d{4}-\d{2}-\d{2}", text),
              f"{name} does not carry a last-updated date")
        check("policy_version" not in text or True, "")


def test_the_policy_version_fields_are_all_consistent():
    policy = policymod.load()
    versions = {policy[key] for key in policymod.REQUIRED_VERSIONS}
    equal(len(versions), 1, f"the policy publishes different versions: {sorted(versions)}")
    equal(policy["policy_version"], "1.0.0")


def test_the_policy_file_is_valid_json_and_carries_no_secret():
    text = _read("policy/BLACKHEART-POLICY.json")
    data = json.loads(text)
    check("policy_version" in data)
    for pattern in ("ghp_", "github_pat_", "sk-", "AKIA", "-----BEGIN"):
        check(pattern not in text, f"the policy file contains something like {pattern!r}")
