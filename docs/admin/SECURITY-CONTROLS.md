# Security controls and credential policy

**For:** administrators adding to this project, and operators handling credentials
**Scope:** the controls that must exist, the invariants that must hold, and the
credential rules
**This document is a specification of what must be true — not a description of an
access-control feature, because there is no such feature**

---

## 1. The invariants

These must hold at all times. A change that breaks one is not a feature.

| # | Invariant | Verified by |
|---|---|---|
| I-1 | No bypass flag exists anywhere in the command surface | `test_policy.py` walks the argument tree; 184 option strings, zero bypass-shaped |
| I-2 | A scope file cannot disable a control | `scope.py` refuses bypass-shaped keys by name |
| I-3 | Every request passes the policy gate and the scope gate | `require_acceptance()` is the first statement of `http_client.request()`; `scope.require()` sits below it |
| I-4 | No credential is embedded in the repository | `validate.py` secrets check |
| I-5 | Nothing acquired is executed, imported or installed | `extract.py`; AST tests assert the absence of the calls |
| I-6 | A blocked resource is recorded as blocked, with no file written | `fetch.py` |
| I-7 | A record that fails its hash check is not counted as evidence | `evidence.py`, `report.py` |
| I-8 | No compliance badge or absolute claim appears in authored content | `test_legal.py` |
| I-9 | No administrative backdoor, master credential or hidden override exists | §2 below — by absence, and by the tests in §3 |

## 2. The backdoor prohibition, in detail

The project must not contain any of the following. Stated as a flat list because
a partial implementation of this list would be worse than none.

```text
FORBIDDEN, without exception:

  hidden administrator passwords
  universal passwords
  master keys
  undocumented bypass switches
  secret CLI flags
  magic HTTP headers that disable a control
  environment-variable backdoors
  emergency credentials embedded in source
  hard-coded administrator credentials
  undocumented authentication bypasses
  any mechanism whose purpose is to make a check not run for some callers
```

### Why this is an invariant and not a preference

Three reasons, and each one alone would be sufficient:

1. **A hidden credential is a single point of failure.** One secret that opens
   many systems converts any leak of it into universal access. A backdoor does not
   add a second lock; it removes the locks.
2. **It contradicts the project's own policy.** Every policy document in this
   repository states that the framework does not bypass access controls. A
   backdoor would make those documents false while they remained published.
3. **It cannot be scoped.** A bypass cannot know whether the caller was authorized
   for *this* target, because that is precisely the check it removes.

### Verified absent, not promised absent

| Check | Command | Result |
|---|---|---|
| No bypass-shaped option string | `python3 workbench/run_tests.py test_policy` | 184 option strings; none contains `ignore`, `bypass`, `skip`, `force`, `unsafe` or `no-policy` |
| No authentication system to bypass | `grep -rniE "def login\|authenticate\(\|is_admin\|privileged_mode" workbench/*.py` | no matches — there is no auth system, no role, no elevation |
| No admin credential accepted anywhere | `grep -rniE "admin\|password" workbench/cli.py` | no matches |
| No roles in the policy | `policy/BLACKHEART-POLICY.json` | no role definition exists |
| No credential in the repository | `python3 .github/scripts/validate.py` | secrets check passes; 15 allowlisted placeholders |

**Run these before and after any change to the command surface.** If one starts
failing, a control has been weakened, and the failure is the finding.

## 3. Credential policy

### Never place these anywhere in the project

Passwords · API keys · tokens · session cookies · private keys · passphrases ·
one-time codes · connection strings containing credentials.

"Anywhere" is literal:

| Location | Why |
|---|---|
| Documentation | It is published. A credential in a doc is a published credential |
| Source code | It ships, and it is copied into forks and caches |
| Examples presented as live credentials | A realistic example is copied and used |
| Fixtures | Test fixtures are read by CI and by contributors |
| Reports | Reports are shared outside the project |
| Git history | History is forever, and public forks keep it after a rewrite |
| Screenshots | Text in an image is not redacted by a text-based scanner |
| CI logs | Logs are retained and often visible to anyone who can read the repository |

### Placeholders

Documentation that must reference a credential uses a placeholder:

```text
<ADMIN_CREDENTIAL>          an administrative credential
<API_TOKEN>                 a service token
<SESSION_COOKIE>            a session cookie value
<PRIVATE_KEY>               a private key
```

A placeholder is never a real value in disguise. Do not write a plausible-looking
string in the placeholder's position, because plausible-looking strings get used.

### If a credential is exposed

```text
1  CLASSIFY   treat it as compromised. Immediately. Not "possibly"
2  ROTATE     revoke the exposed value and issue a new one
3  REPLACE    through the legitimate credential-management mechanism — a secret
              manager, an environment variable injected at runtime, an OIDC
              token. NOT by committing a new value
4  RECORD     the incident, the rotation, and the date — and never the exposed
              value itself. The record says "the credential issued on <date> was
              exposed in <place> and rotated"; it does not reproduce it
5  CHECK      whether the exposure reached a fork, a cache, a CI log or an
              artifact, and act on each
```

**Rotating is not optional and not deferrable.** A credential that has been in a
transcript, a screenshot or a log has been exposed, whether or not anyone read it.

### Confirmation over a concrete case

A credential was supplied in the request that commissioned this documentation
layer, as an "administrator password" for the framework.

| Question | Answer |
|---|---|
| Was it written into the repository? | **No.** It appears in no file, and will not |
| Did it already exist in the repository or its history? | **No.** Searched the working tree, all refs' commit content, and the secrets gate: absent |
| Does it grant anything? | **No.** There is no administrator account, no admin login and no privileged mode in this framework. The string cannot unlock anything here |
| What must happen to it? | **Treat as compromised and rotate it.** It was transmitted in plain text over a chat interface and now exists in that record. If the same value is in use anywhere real — a password manager, a server, an account — rotate it now |

**No replacement password was committed**, and none will be. Adding one would
violate the prohibition in §2 and would not make the framework safer — it would
make a single string worth stealing.

## 4. Secret management

Where the project's architecture supports it:

| Practice | Detail |
|---|---|
| Secrets injected at runtime | Environment variables or a secret manager, never a file in the repository |
| Least privilege | A credential for a task gets the minimum scope that task needs |
| Rotation | On a schedule, and immediately on any suspected exposure |
| Separation | Test credentials are not production credentials |
| No shared credentials | One identity per operator; a shared credential has no accountable holder |
| Scoped tokens | Prefer a token limited to one repository or one service over a general-purpose one |

The workbench's own credential handling follows the same shape: a value passed
with `--secret` is redacted wherever it appears, and header values named in
`SENSITIVE_HEADERS` are redacted by name before anything is written. That is
output hygiene, not secret management — it protects the evidence, not the target.

## 5. What these controls are not

- **They are not an access-control system.** This framework has no access-control
  system. It has a scope gate that checks what an operator asserted, and a policy
  acknowledgement that records what was read.
- **They are not a substitute for authorization.** No control in this document
  establishes that someone may test anything.
- **They are not enforceable against a hostile operator.** Someone who can edit
  the code can remove a gate. What stops that is review — the checks in §2's table,
  the review checklist, and the fact that the change would be visible in a diff.

That last point is the honest one. The invariants in §1 protect against accident
and against drift. Against a determined insider who can change the code, the
control is that the change is reviewable, and someone has to read it.
