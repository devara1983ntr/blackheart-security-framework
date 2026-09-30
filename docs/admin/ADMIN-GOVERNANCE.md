# Administrative governance

**For:** repository administrators, framework operators, and the people who
authorize them
**Scope:** the identity model, the authority/authorization boundary, the
backdoor prohibition, and where responsibility sits
**Sources:** every claim about the software was verified against `workbench/`;
every claim about governance is a rule this project sets for itself

---

## 1. Authority is not authorization

Two different things, routinely conflated, and the confusion is how authorized
work becomes unauthorized:

| | **Administrative authority** | **Target authorization** |
|---|---|---|
| Over what | This software: its code, its policy, its CI, its releases, a running instance | A specific system, its data, its accounts |
| Granted by | Being responsible for the project | A person or entity entitled to grant it |
| Recorded in | The repository, its policy documents, its history | An authorization record, mirrored into a scope file |
| Lets you | Change what the tool does | Send requests to that target, within the grant |
| Does **not** let you | Test anything | Anything the grant does not cover |

**A repository administrator may control the BLACKHEART project and does not
thereby acquire authorization over arbitrary external systems.**

That sentence is the whole of §1. Everything below elaborates it.

## 2. The purpose of an administrative role

Administration exists to **narrow** what is permitted, never to widen it:

- to set policy that operators must follow;
- to define which kinds of work require elevated review;
- to require records of who authorized what, for how long;
- to stop work that has lost its authorization;
- to keep evidence intact and handle it correctly.

An administrative role that widens access — a bypass, an override, a master
credential — is not an administrative feature. It is the threat this document
exists to prevent. See §5.

## 3. The four roles

### 3.1 Repository administrator

**Controls:** the project. Merges changes, sets policy, owns the release.

**May not:** treat that control as permission over any external system. May not
add a bypass to the tool "for administrators". May not represent the project as
having authorized anyone's activity.

**Governing rule:** the administrator's power is over the *software*, and the
software's own policy forbids the bypass. An administrator who adds one has
changed the software into a different one, and the disclaimer, the terms and the
acceptable-use policy all continue to describe the original.

### 3.2 Framework operator

**Controls:** a running instance. Writes the scope file, sets the budget, keeps
the evidence.

**May not:** widen the scope beyond what the authorization permits. The scope file
is an assertion of authority the operator was given — not a document the operator
invents.

> **The scope file is the operator's assertion, and the tool checks its
> arithmetic, not its truth.** No administrative role changes that. If an operator
> writes a host into a scope file they were not authorized to test, the tool will
> send the request and the operator will have acted without authorization. Nothing
> in this framework prevents it, and no document should imply otherwise.

### 3.3 Authorized security tester

**Controls:** nothing by role. Their permission comes entirely from the
authorization record — which names the target, the methods, the window and the
limits.

**May not:** act outside that record, however senior they are in the project.
Seniority is not scope. A tester who is also the repository administrator has
exactly the authorization of a tester who is not.

### 3.4 Target / resource owner

**Controls:** access to their own systems and resources, and who may test them.

**This is the only role whose permission creates target authorization.** Every
other role's permission is derived from this one, and only as far as this one
grants it.

## 4. There is no administrator account, and that is deliberate

**Verified against the implementation:**

| Question | Answer |
|---|---|
| Is there an administrator account, login, or password? | **No.** No authentication system exists in `workbench/` |
| Is there a role, a privileged mode, or an elevation path? | **No.** No role check, no privileged flag, no elevation |
| Does any command accept an admin credential? | **No.** No command takes a password or an admin token |
| Does the policy define roles? | **No.** `policy/BLACKHEART-POLICY.json` defines none |
| Does the acceptance record identity? | **No,** and the policy requires it not to: `acceptance.collects_identity` must be `false` |

So "administrator" in these documents is an **organisational role**, not a
technical one. It describes who is responsible for a decision, not a credential
that unlocks anything.

**This is the design position, not an omission.** An administrator bypass would be
a single point of failure that converts any compromise of one credential into
access to every target, and it would put the project's own policy in direct
contradiction with its code. §5 forbids it explicitly.

## 5. The backdoor prohibition (invariant)

This project **must not** contain, and an administrator must not add:

| Forbidden | Because |
|---|---|
| Hidden administrator passwords | A hidden credential is a backdoor by definition |
| Universal or master passwords | One secret that opens many systems is the threat model, not a feature |
| Master keys | Same |
| Undocumented bypass switches | A capability the policy says does not exist |
| Secret CLI flags | Same, and worse: invisible in `--help` |
| Magic HTTP headers | A header that disables a control is a bypass wearing a protocol's clothes |
| Environment-variable backdoors | A variable that grants access is a backdoor |
| Emergency credentials embedded in source | Credentials belong in a secret manager, never in code |
| Hard-coded administrator credentials | Same |
| Undocumented authentication bypasses | Same, in its plainest form |

**Administrative authority must never be implemented as a hidden bypass.**

### How the prohibition is verified rather than asserted

The project checks this rather than promising it:

| Check | What it proves |
|---|---|
| `workbench/tests/test_policy.py` walks the entire argument tree and fails if any option string contains `ignore`, `bypass`, `skip`, `force`, `unsafe` or `no-policy` | No bypass flag exists in the command surface — **184 option strings, zero bypass-shaped** |
| The scope loader refuses a scope file containing a bypass-shaped key, by name | A control cannot be disabled from a configuration file |
| The policy acceptance gate is the first statement of `http_client.request()` | One gate at the socket, not a per-command convention |
| `validate.py`'s secrets check scans for credential-shaped material | No credential is embedded in the repository |
| `test_legal.py` fails on compliance badges and absolute claims | The project does not overstate itself |

Run them:

```bash
python3 workbench/run_tests.py test_policy      # the bypass surface, asserted absent
python3 .github/scripts/validate.py             # secrets, links, index, history
```

**An invitation to add any row of the table above is an invitation to break these
tests.** They were written to fail if one appears, and that is the enforcement.

## 6. Credential policy (summary)

The full policy is [`SECURITY-CONTROLS.md`](SECURITY-CONTROLS.md) §2. In one
paragraph: passwords, API keys, tokens, session cookies and private keys never
enter documentation, source, examples, fixtures, reports, Git history, screenshots
or CI logs. If a credential is exposed anywhere, it is classified as compromised,
rotated, and replaced through the legitimate credential-management mechanism — and
the exposed value is **not** reproduced in the documentation that records the
incident. Documentation uses placeholders such as `<ADMIN_CREDENTIAL>`, and a
placeholder is never a real value in disguise.

## 7. Responsibility, and what is not claimed

**Project identification.** BLACKHEART Security Framework · GitHub owner
`devara1983ntr` · author Roshan. No company, legal entity, registered office,
counsel or certification is invented anywhere in this layer.

**Administrators and operators remain responsible for:** their authorization,
their selection of targets, their scope, their credentials, the data they handle,
what they download, their compliance with applicable law, and the operational
impact of what they run.

**Not claimed:** that the author is legally immune from any use of the framework.
No absolute claim of that kind appears in these documents, and any that did would
be deleted. Liability and responsibility are allocated as
[`TERMS-OF-USE.md`](../../TERMS-OF-USE.md) §11 sets out, and the effect of any of
it depends on the law that applies to you — which this project does not determine.

## 8. Policy consistency

This layer was written against the existing documentation and does not contradict
it. Checked, specifically:

| Against | Consistent because |
|---|---|
| Phase 5 agent rules | This layer restates the prohibitions and adds review requirements on top; it removes none |
| `ACCEPTABLE-USE.md` | The prohibited list is unchanged; §"Prohibited" of that document remains the operative list |
| `AUTHORIZATION-AGREEMENT.md` | This layer uses that record rather than inventing a second one, except for the bounded emergency case, which is a companion template |
| `DOWNLOAD-AND-ACQUISITION-POLICY.md` | The blocking statuses and refusal routes are unchanged; this layer adds who must review, not what is blocked |
| `PRIVACY-POLICY.md` | No new collection is introduced. The administrative record is local and holds no target data |
| `AI-AGENT-TERMS.md` | Addressed again to agents in an administrative context, with the same obligations |

Where any of those and this layer could be read as disagreeing, **the stricter
document controls** — and it is always the earlier policy, because this layer can
only add.
