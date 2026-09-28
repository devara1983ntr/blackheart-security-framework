# Blackhearts Adapter — `senior-fullstack`

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `engineering-team/skills/senior-fullstack` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-28 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Security audit | **FAIL** — 2 critical, 9 high, 0 info |
| Classification | engineering-and-delivery |
| Priority | P3 - engineering and delivery |
| Contents | 6 markdown files, 3 scripts |
| Governing policy | [SKILL.md](../../../../../conformance/SKILL.md) |

## What this adapter is for

This file is Blackhearts-local metadata. The skill directory itself is **unmodified upstream content**. It records provenance, the audit result, and the conditions under which the skill may be used inside a Blackhearts engagement.

## Evidence status

Per the governing conformance policy, **any match this skill reports is `UNVERIFIED` until it is independently demonstrated.** Loading this skill does not authorize it to scan, test, or touch any target. A skill's own severity rating is **not** a Blackhearts severity.

## Audit adjudication

The upstream auditor returned **FAIL** with 11 raw finding(s). Categories: `DEPS-RUNTIME` (9), `CRED-HARVEST` (2).

| Category | Assessment |
|---|---|
| `DEPS-RUNTIME` (9) | Third-party imports in example/tooling code. See Skills/VENDOR.md for the dependency policy. |
| `CRED-HARVEST` (2) | Environment-variable reads matched in template/example code, not harvesting logic. |

<details><summary>Raw findings as reported by the auditor</summary>

| Sev | Category | Location | Pattern |
|---|---|---|---|
| CRITICAL | `CRED-HARVEST` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:524` | `SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me")` |
| CRITICAL | `CRED-HARVEST` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:558` | `"PASSWORD": os.environ.get("DB_PASSWORD", "password"),` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:661` | `RUN npm install` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:673` | `npm install` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:773` | `"nextjs": [f"cd {name}", "npm install", "cp .env.example .env.local", "npm run dev"],` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:777` | `"cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload",` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:778` | `"cd frontend && npm install && npm run dev"` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:783` | `"cd server && npm install && npm run dev",` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:784` | `"cd client && npm install && npm run dev"` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:789` | `"cd backend && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver",` |
| HIGH | `DEPS-RUNTIME` | `engineering-team/skills/senior-fullstack/scripts/project_scaffolder.py:790` | `"cd frontend && npm install && npm run dev"` |

</details>

**Manual adjudication.** 2 CRED-HARVEST findings are scaffolder template placeholders `os.environ.get("DJANGO_SECRET_KEY", "change-me")` — a default value, no exfiltration.

## Known defects

None found. All local links in this skill resolve.

## Conditions of use

1. Read [`skills/conformance/SKILL.md`](../../../../../conformance/SKILL.md) before any use. It governs authorization, evidence status, severity, and secrets handling.
2. No target may be scanned, tested, or profiled until the operator supplies the target and explicit authorization, in writing, in the engagement record.
3. Do not execute any script from this skill against a third-party system without that authorization. Scripts are third-party code with third-party defects.
4. Report every result as `UNVERIFIED` until independently demonstrated, and record rejected hypotheses alongside confirmed findings.
5. Record the skill name, upstream commit, and this adapter path in the evidence log so any finding can be traced back to the exact tool version that produced it.

## Provenance

- Licence text: [claude-skills-LICENSE](../../../../../licenses/claude-skills-LICENSE)
- Full provenance and integration record: [VENDOR.md](../../../../../VENDOR.md)
- Regenerate with the mirror audit workflow; see `.github/workflows/upstream-sync.yml`.
