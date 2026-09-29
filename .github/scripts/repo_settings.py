#!/usr/bin/env python3
"""Apply the GitHub repository settings this project requires, in one pass.

Run:  GH_TOKEN=<token> python3 .github/scripts/repo_settings.py [--dry-run]

Every action is idempotent: running it twice changes nothing the second time.
The token is read from the environment and is never written to a file, a
config, the remote URL, or this repository. It needs `repo` and `admin:repo_hook`
scope for the branch protection rules.

What it sets, and why each one matters here:

  description      The repository page is read before the README. It has to
                   name the project and its purpose in one line.
  topics           Topics are the only free-text search index GitHub offers a
                   repository. Without them the project is findable only by
                   its exact name.
  branch protection  `main` is the publication target for GitHub Pages and the
                   integrity gate runs in CI. The rules below require CI to
                   pass and forbid force-push, which is what keeps a rewritten
                   history from reaching the published site unnoticed.
  stale branch     `jules-14349490603005815930-7a465791` is a bot branch whose
                   tip is fully merged into main (verified via
                   `GET /compare/main...<sha>`: ahead_by 0, behind_by 31). It
                   is deleted only after that comparison is re-run here, so
                   this script refuses to delete a branch that has drifted.
"""
import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "devara1983ntr"
REPO = "blackheart-security-framework"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

DESCRIPTION = (
    "Governed security-supply-chain framework for AI agents: 388 pinned skills, "
    "39 commands and 33 personas, each behind a reviewed adapter and a "
    "CI-enforced authorization gate."
)

# GitHub accepts at most 20 topics. These are the 20 a reader would
# actually search for; a 21st would make the whole call fail with 422.
TOPICS = [
    "ai-security", "agent-security", "supply-chain-security", "llm-security",
    "prompt-injection", "security-framework", "agent-governance",
    "guardrails", "devsecops", "mitre-atlas", "owasp", "red-team",
    "threat-modeling", "static-analysis", "pentesting",
    "skill-governance", "supply-chain", "security-tools", "claude-skills",
    "github-actions",
]

STALE_BRANCH = "jules-14349490603005815930-7a465791"
MAIN = "main"

DRY = "--dry-run" in sys.argv
token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    sys.exit("Set GH_TOKEN in the environment. Do not pass it as an argument — "
             "arguments land in the shell history and in /proc.")


def call(method, path, body=None):
    # "" and "/" both mean "the repository itself" -- the repo URL with a
    # trailing slash 404s on PATCH, so normalise it away.
    if path in ("", "/"):
        url = API
    elif path.startswith("/"):
        url = API + path
    else:
        url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "blackheart-repo-settings",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


results = []


def record(name, status, detail=""):
    results.append((name, status, detail))
    print(f"  {status:>6}  {name}" + (f"  — {detail}" if detail else ""))


print("=" * 68)
print("  REPOSITORY SETTINGS")
print("=" * 68)

# ---- description ----------------------------------------------------------
if DRY:
    record("description", "DRY", DESCRIPTION[:52] + "…")
else:
    code, body = call("PATCH", "", {"description": DESCRIPTION})
    record("description", "OK" if code == 200 else f"FAIL {code}", str(body)[:120])

# ---- topics ---------------------------------------------------------------
# The topics endpoint replaces the whole set, so send the full list.
if DRY:
    record("topics", "DRY", f"{len(TOPICS)} topics")
else:
    code, body = call("PUT", "/topics",
                      {"names": TOPICS})
    record("topics", "OK" if code in (200, 204) else f"FAIL {code}", str(body)[:120])

# ---- branch protection on main -------------------------------------------
# No force-push, and CI must be green, so history cannot be rewritten onto the
# published branch without the workflows being re-run against the new tree.
RULES = {
    "required_status_checks": {
        "strict": True,
        "contexts": ["validate", "Build and deploy"],
    },
    "enforce_admins": True,
    "required_pull_request_reviews": None,
    "restrictions": None,
    "required_linear_history": False,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "required_conversation_resolution": True,
    "block_creations": False,
}
# Both keys must be present in the request body -- omitting them is a 422,
# not a "use the default". null is the documented value for "not required".
assert "required_pull_request_reviews" in RULES and "restrictions" in RULES

if DRY:
    record("branch protection: main", "DRY",
           "require CI, block force-push and deletion")
else:
    code, body = call("PUT", f"/branches/{MAIN}/protection", RULES)
    if code == 422 and isinstance(body, str) and "private" in body.lower():
        # Branch protection is only available on public repos under free plans
        # in some configurations; report it honestly rather than failing silently.
        record("branch protection: main", "SKIP",
               "API refused the rule set — set it by hand in Settings → Branches")
    else:
        record("branch protection: main", "OK" if code in (200, 201) else f"FAIL {code}",
               str(body)[:160])

# ---- stale branch ---------------------------------------------------------
# Never blind-delete. Re-verify that the branch tip is an ancestor of main.
if DRY:
    record(f"delete {STALE_BRANCH}", "DRY", "would verify merge, then delete")
else:
    code, body = call("GET", f"/branches/{STALE_BRANCH}")
    if code != 200:
        record(f"delete {STALE_BRANCH}", "SKIP",
               "branch already gone" if code == 404 else f"lookup failed {code}")
    else:
        sha = body["commit"]["sha"]
        _, cmp = call("GET", f"/compare/{MAIN}...{sha}")
        ahead = cmp.get("ahead_by") if isinstance(cmp, dict) else None
        if ahead != 0:
            record(f"delete {STALE_BRANCH}", "REFUSED",
                   f"branch has {ahead} commit(s) not in main — not deleting")
        else:
            code, body = call("DELETE", f"/git/refs/heads/{STALE_BRANCH}")
            record(f"delete {STALE_BRANCH}",
                   "OK" if code == 204 else f"FAIL {code}",
                   f"tip {sha[:7]} fully merged, ahead_by 0")

print("=" * 68)
bad = [r for r in results if r[1].startswith(("FAIL", "REFUSED"))]
print(f"  {len(results) - len(bad)}/{len(results)} applied cleanly")
print("=" * 68)
sys.exit(1 if bad else 0)
