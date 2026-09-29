#!/usr/bin/env python3
"""Parse every Blackhearts-authored configuration file, and check the shape of
the workflows.

    python3 .github/scripts/check_authored_config.py
    python3 .github/scripts/check_authored_config.py --json

Why this exists
---------------
This repository's entire protection is its CI: an eight-check validator, a
twenty-group audit, a link check, a browser suite, and the workflows that run
them. GitHub does not run a workflow whose YAML it cannot parse — it reports the
error in the Actions tab and the repository keeps looking fine. A file that
silently disables the control protecting everything else is the one class of
defect no gate here could previously see, because every gate is *inside* the
thing that breaks.

So this checks the gates. Two questions, both mechanical:

  1. Does every authored YAML, JSON and JSON5 file parse at all?
  2. Does every workflow have the three keys GitHub requires (`name`, `on`,
     `jobs`), and does every job have a runner and at least one step?

Scope: Blackhearts-authored configuration only. The vendored mirror and the
catalogue are pinned upstream content, verified byte-for-byte by
`validate.py` — this gate never reads them, and never "fixes" them.

Exit codes:  0 = every authored configuration file parsed and is well-formed,
             1 = at least one did not.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP_DIRS = {".git", "node_modules", "__pycache__", "third-party", "catalog",
             ".venv", "venv", "dist", "build"}
SKIP_PREFIXES = ("skills/third-party/", "skills/catalog/")

WORKFLOW_DIR = os.path.join(REPO, ".github", "workflows")

# A repository path named in a `run:` or `uses:` value: a token containing a
# slash that ends in .py. Shape checks alone cannot see a workflow that calls a
# script which has since been renamed: that workflow parses perfectly and fails
# at three in the morning.
SCRIPT_RE = re.compile(r"(?<![\w./-])((?:\.[\w-]+/|[\w-]+/)+[\w.-]+\.py)\b")


def authored_config_files():
    out = []
    for dp, dn, fn in os.walk(REPO):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), REPO).replace(os.sep, "/")
            if rel.startswith(SKIP_PREFIXES):
                continue
            if f.endswith((".yml", ".yaml", ".json", ".json5")):
                out.append(rel)
    return sorted(out)


def parse_yaml(path):
    import yaml
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def parse_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_json5(path):
    import json5
    with open(path, encoding="utf-8") as fh:
        return json5.load(fh)


PARSERS = {".yml": parse_yaml, ".yaml": parse_yaml,
           ".json": parse_json, ".json5": parse_json5}


def check_workflow(rel, doc):
    """The three keys GitHub requires, plus a runner and a step per job.

    `on` is looked up as both the string "on" and the boolean True: PyYAML
    implements YAML 1.1, in which the unquoted key `on` is a boolean. Reading
    only `doc["on"]` would report every valid workflow in this repository as
    missing its trigger.
    """
    problems = []
    if not isinstance(doc, dict):
        return [f"{rel}: top level is not a mapping"]
    if "name" not in doc:
        problems.append(f"{rel}: no `name` key")
    if "on" not in doc and True not in doc:
        problems.append(f"{rel}: no `on` trigger")
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        problems.append(f"{rel}: no `jobs` key, or it is empty")
        return problems
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            problems.append(f"{rel}: job `{job_name}` is not a mapping")
            continue
        if "runs-on" not in job:
            problems.append(f"{rel}: job `{job_name}` has no `runs-on`")
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            problems.append(f"{rel}: job `{job_name}` has no steps")
            continue
        for i, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                problems.append(f"{rel}: job `{job_name}` step {i} is not a mapping")
            elif "uses" not in step and "run" not in step:
                problems.append(f"{rel}: job `{job_name}` step {i} has neither "
                                f"`uses` nor `run`")
    problems.extend(check_referenced_scripts(rel, doc))
    return problems


def check_referenced_scripts(rel, doc):
    """Every repository script a workflow names must exist, and be executable.

    Read-only: this resolves paths, it does not run anything.
    """
    problems, seen = [], set()
    blob = json.dumps(doc)
    for match in SCRIPT_RE.finditer(blob):
        token = match.group(1)
        if token in seen or token.startswith(("http", "/")):
            continue
        seen.add(token)
        path = os.path.join(REPO, token)
        if not os.path.isfile(path):
            problems.append(f"{rel}: references `{token}`, which does not exist")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    args = ap.parse_args()

    files = authored_config_files()
    failures, parsed, by_kind = [], 0, {}
    for rel in files:
        ext = os.path.splitext(rel)[1]
        by_kind[ext] = by_kind.get(ext, 0) + 1
        parser = PARSERS.get(ext)
        if parser is None:
            continue
        path = os.path.join(REPO, rel)
        try:
            doc = parser(path)
        except ImportError as exc:              # a missing parser is a gate error,
            failures.append(f"{rel}: parser unavailable ({exc})")   # not a pass
            continue
        except Exception as exc:
            failures.append(f"{rel}: does not parse — {type(exc).__name__}: "
                            f"{str(exc).splitlines()[0][:160]}")
            continue
        parsed += 1
        if rel.startswith(".github/workflows/") and ext in (".yml", ".yaml"):
            failures.extend(check_workflow(rel, doc))

    report = {
        "authored_config_files": len(files),
        "parsed": parsed,
        "by_kind": by_kind,
        "failures": failures,
        "skipped_vendored": ["skills/third-party/", "skills/catalog/"],
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Blackhearts authored configuration")
        print("=" * 66)
        print(f"  files found     : {len(files)}")
        print(f"  parsed          : {parsed}")
        print(f"  by kind         : {', '.join(f'{k} {v}' for k, v in sorted(by_kind.items()))}")
        if failures:
            print(f"  FAILURES        : {len(failures)}")
            for f in failures:
                print(f"      {f}")
        else:
            print("  RESULT          : every authored configuration file parses, "
                  "and every workflow is well-formed")
        print("=" * 66)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
