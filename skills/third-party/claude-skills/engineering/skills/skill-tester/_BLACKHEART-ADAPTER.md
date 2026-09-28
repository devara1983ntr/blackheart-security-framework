# Blackhearts Adapter — `skill-tester`

| Field | Value |
|---|---|
| Upstream | `https://github.com/alirezarezvani/claude-skills` |
| Upstream commit | `19392f7a08264ed00486a251f5b2098321771f94` |
| Upstream path | `engineering/skills/skill-tester` |
| Upstream licence | MIT (c) 2025 Alireza Rezvani |
| Integrity | byte-identical to upstream, verified 2026-09-28 |
| Modified by Blackhearts | No — this `_BLACKHEART-ADAPTER.md` is the only added file |
| Security audit | **FAIL** — 13 critical, 0 high, 0 info |
| Classification | engineering-and-delivery |
| Priority | P3 - engineering and delivery |
| Contents | 8 markdown files, 6 scripts |
| Governing policy | [SKILL.md](../../../../../conformance/SKILL.md) |

## What this adapter is for

This file is Blackhearts-local metadata. The skill directory itself is **unmodified upstream content**. It records provenance, the audit result, and the conditions under which the skill may be used inside a Blackhearts engagement.

## Evidence status

Per the governing conformance policy, **any match this skill reports is `UNVERIFIED` until it is independently demonstrated.** Loading this skill does not authorize it to scan, test, or touch any target. A skill's own severity rating is **not** a Blackhearts severity.

## Audit adjudication

The upstream auditor returned **FAIL** with 13 raw finding(s). Categories: `CMD-INJECT` (6), `CODE-EXEC` (6), `CRED-HARVEST` (1).

| Category | Assessment |
|---|---|
| `CMD-INJECT` (6) | Command execution via `child_process`/`os.system` — used to drive browsers and tooling. Inputs are not attacker-controlled in the documented usage. |
| `CODE-EXEC` (6) | Dynamic-import / eval patterns. See adjudication above where applicable. |
| `CRED-HARVEST` (1) | Environment-variable reads matched in template/example code, not harvesting logic. |

<details><summary>Raw findings as reported by the auditor</summary>

| Sev | Category | Location | Pattern |
|---|---|---|---|
| CRITICAL | `CMD-INJECT` | `engineering/skills/skill-tester/scripts/security_scorer.py:429` | `- os.system(), os.popen() usage` |
| CRITICAL | `CMD-INJECT` | `engineering/skills/skill-tester/scripts/security_scorer.py:429` | `- os.system(), os.popen() usage` |
| CRITICAL | `CODE-EXEC` | `engineering/skills/skill-tester/scripts/security_scorer.py:431` | `- eval(), exec() usage` |
| CRITICAL | `CODE-EXEC` | `engineering/skills/skill-tester/scripts/security_scorer.py:431` | `- eval(), exec() usage` |
| CRITICAL | `CMD-INJECT` | `engineering/skills/skill-tester/tests/test_security_scorer.py:123` | `code = 'os.system("ls -la")'` |
| CRITICAL | `CODE-EXEC` | `engineering/skills/skill-tester/tests/test_security_scorer.py:128` | `code = 'result = eval(user_input)'` |
| CRITICAL | `CODE-EXEC` | `engineering/skills/skill-tester/tests/test_security_scorer.py:133` | `code = 'exec(user_code)'` |
| CRITICAL | `CMD-INJECT` | `engineering/skills/skill-tester/tests/test_security_scorer.py:138` | `code = 'subprocess.run(cmd, shell=True)'` |
| CRITICAL | `CRED-HARVEST` | `engineering/skills/skill-tester/tests/test_security_scorer.py:297` | `api_key = os.environ.get("API_KEY")` |
| CRITICAL | `CMD-INJECT` | `engineering/skills/skill-tester/tests/test_security_scorer.py:441` | `os.system("echo " + user_input)` |
| CRITICAL | `CMD-INJECT` | `engineering/skills/skill-tester/tests/test_security_scorer.py:464` | `subprocess.run(cmd, shell=True)` |
| CRITICAL | `CODE-EXEC` | `engineering/skills/skill-tester/tests/test_security_scorer.py:486` | `return eval(user_input)` |
| CRITICAL | `CODE-EXEC` | `engineering/skills/skill-tester/tests/test_security_scorer.py:507` | `exec(user_code)` |

</details>

**Manual adjudication.** All 13 CRITICAL findings are **false positives**: they are the detection strings of the skill's own `security_scorer.py` (a tool that *looks for* `os.system`/`popen`/`shell=True`) plus its test fixtures that contain those patterns as literal data. A security scanner flagging its own signatures.

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
