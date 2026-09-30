# Workbench operations for agents

**Applies to:** any agent driving `workbench/cli.py`
**Read with:** [`PHASE5-SAFETY-RULES.md`](PHASE5-SAFETY-RULES.md) first, then the
command reference in [`../workbench/COMMANDS.md`](../workbench/COMMANDS.md)
**Purpose:** what each capability does, what it refuses, and what an agent must do
when it refuses. No command here is described in more depth than the command
reference; this document is the agent-facing orientation.

---

## The order, every time

Eleven steps. Nothing in the workbench checks that an agent followed them, which
is exactly why they are written down: the check is the agent's own discipline, and
step 10 is where it is paid for.

```text
 1. Read the rules            docs/agent/PHASE5-SAFETY-RULES.md, ACCEPTABLE-USE.md
 2. Read the policy           policy/BLACKHEART-POLICY.json and the documents it names
 3. Check the version         blackheart policy status
 4. Accept, if not accepted   blackheart policy accept
 5. Local or active?          active = anything that reaches a network target
 6. Establish scope           the authorization record, written into a scope file
 7. Validate the target       blackheart scope validate --scope scope.json
 8. Execute within limits     budgets, intervals, methods, exclusions, cancellation
 9. Record evidence           the history, the manifest, the bundle — as you go
10. Stop on ambiguity         any unclear authorization, refusal, or strain
11. Report honestly          observations, limitations, refusals, and what was not tested
```

Steps 1–4 are prerequisites for steps 5–8. Step 5 is not decoration: a local
read-only operation (parse, hash, report from existing evidence) may run without
policy acceptance or scope, and that exemption exists so that analysis of evidence
someone else collected does not need a network authorization. **The exemption ends
the moment a socket would be opened.** The exhaustive list is
`policy/BLACKHEART-POLICY.json` → `exempt_operations`, and it is tested against
the command parser rather than trusted.

## Policy commands

| Command | Purpose | Agent note |
|---|---|---|
| `blackheart policy status` | Is an acceptance recorded, and is it current? | Exit 1 when not accepted. Run before any active work |
| `blackheart policy accept` | Record acceptance of the current policy version | A local record. No identity, nothing transmitted |
| `blackheart policy validate` | Does the policy parse, and do the ten documents it names exist? | Exit 1 with the missing document named |
| `blackheart policy show` | Print the policy | Read-only |

A policy change invalidates prior acceptance by content hash, so an old record
does not carry forward. If `status` says stale, the answer is `accept` — by a
person who has read the change — never a workaround.

## Scope

`scope validate --scope scope.json` prints what will be enforced: hosts, paths,
exclusions, methods, budget, interval, window. **An agent must read that output
rather than assume it.** The realistic agent failure is not skipping the check but
never noticing there was one.

A scope file without a positive `max_requests` is refused — an unbounded request
budget is not a scope. Exit codes: `0` ran, `1` failed, `2` usage or malformed
scope, `3` refused by scope.

## Capability map

| Capability | Commands | What it will refuse |
|---|---|---|
| **HTTP** | `http inspect`, `http replay`, `http diff` | Hosts, paths, methods or budgets outside the scope; write methods without explicit confirmation; addresses in private, loopback, link-local or multicast ranges without the private-network opt-in; redirects that leave scope, hop by hop |
| **API testing** | `api inspect`, `api discover` | The same scope rules; no auth bypass, no forced browsing, no token reuse beyond what was supplied |
| **Discovery** | `web crawl`, `web scan`, `api discover` | Crawling off-host, out of scope, past the page and depth caps, or into excluded paths; it records what it declines to follow |
| **Fuzzing** | `http fuzz`, `http mutate` | Out-of-scope targets, unbounded mutations, more than one request in flight by default, write methods without confirmation; it stops on cancellation between requests |
| **Acquisition** | `resource download` | `401`/`402`/`403`/`407`/`451`, paywalls, challenges, DRM and licence markers, expired signed URLs — recorded as `blocked` with the authorized route and **no file written** |
| **Extraction** | `resource extract` | Manifest-hash mismatches (refused before parsing), traversal members, absolute paths, symlinks, hardlinks, device nodes, archives over the size, count, ratio or depth limits. Nothing is ever executed |
| **Evidence** | `evidence hash`, `evidence manifest`, `report generate`, `resource inspect` | Records that fail their own hash check are not adopted into a report's counts; a report says which records did not verify |
| **Emergency** | `emergency collect` | Anything but `GET`/`HEAD`; its budget is `min(scope.max_requests, 20)`; it exists for one bounded check, not for volume |

## When the workbench refuses

A refusal is a result. The agent records it and moves on; it does not look for
another way to the same resource.

| Refusal | What the agent records | What the agent does next |
|---|---|---|
| Scope refusal (exit 3) | The decision, the value that failed, and the scope it was checked against | Report. Do not edit the scope file to fit |
| `401`/`403`/`407` | Status, headers that explain it, the URL, the time | Name the authorized route, stop the path |
| `402`/`451`, paywall or licence marker | Same, plus the marker | Stop the path. Do not look for another copy |
| Challenge interstitial | The marker, and that the response is not evidence of the resource | Stop the path |
| Budget or window exhausted | The counts and the limit reached | Stop the run, report |
| Policy not accepted / stale | The reason `policy status` gave | Tell the operator. Never work around it |
| Evidence hash mismatch | The record id and both hashes | Do not quote the record; report that it failed verification |

## The decision tree

Deterministic, so that two agents facing the same state reach the same answer:

```text
Is the operation local and read-only (parse, hash, report from existing evidence)?
├─ yes ─────────────────────────────► run it. No scope or acceptance needed
└─ no  (it would open a socket)
   │
   Is the policy accepted on this machine, and current?
   ├─ no  ──────────────────────────► STOP. Report the policy status reason
   └─ yes
      │
      Is there a scope file for this target?
      ├─ no  ───────────────────────► STOP. Authorization is not established
      └─ yes
         │
         Does `scope validate` accept it, and does it cover this target and method?
         ├─ no  ────────────────────► STOP. Record the scope decision verbatim
         └─ yes
            │
            Does the target respond with a refusal or a challenge?
            ├─ yes ─────────────────► record status + reason, name the authorized
            │                         route, STOP that path
            └─ no
               │
               Within budget, window, rate limit, and free of target strain?
               ├─ no  ──────────────► STOP the run, report the counts
               └─ yes ─────────────► execute, record, continue
```

A branch that says STOP is not a failure of the run. It is the run.

## What an agent must never do with these commands

- Never edit a scope file to make a request pass. Editing scope is an
  authorization decision and belongs to the person who granted it.
- Never re-run with a different header, method or encoding after a refusal.
- Never treat `policy accept` as authorization, and never run it silently on
  someone else's machine to unblock a run.
- Never report a `blocked` acquisition as a finding, or a `refused` extraction as
  a failure of the target.
- Never continue past a stop condition because the run is nearly finished.
