# Responsible Use

**Project:** BLACKHEART Security Framework · **Author:** Roshan
**Last updated:** 2026-09-30

---

Practical guidance for using the workbench without causing harm, losing control
of your evidence, or turning an authorized engagement into an unauthorized one.
It assumes you have read [`ACCEPTABLE-USE.md`](ACCEPTABLE-USE.md) and that you
hold authorization for what you are about to test.

## Before you send anything

1. **Write the scope file first, from the authorization, not from memory.** If you
   are filling in `allowed_hosts` and cannot point at the line in the agreement
   that names a host, it is not in scope.
2. **Check the file loads, and read what it will enforce.**
   ```bash
   python3 -m workbench.cli scope validate --scope scope.json
   ```
   It prints the hosts, methods, budget, interval and window it will apply. If any
   of those is not what the authorization says, fix the file.
3. **Accept the policy on the machine you will run from.** Active operations are
   refused without it, by design:
   ```bash
   python3 -m workbench.cli policy accept
   python3 -m workbench.cli policy status
   ```
   Acceptance records that you read the rules. It is not authorization for
   anything.
4. **Plan the destructive and the load-bearing.** Anything that changes state, and
   anything that sends volume, deserves a written ceiling and a decision made
   before the run rather than during it.

## While you are testing

| Do | Because |
|---|---|
| Keep the request budget and interval from the authorization, not from what the tool allows | The tool's defaults are conservative, not authoritative |
| Use a dedicated history file per target | A mixed history is hard to attribute and easy to mislead with |
| Name your own credentials with `--secret` | Redaction by header name does not catch a token in a URL or a body |
| Record the authorization context (which identity you used) with the observations | An authorization-boundary observation means nothing without knowing whose access it was |
| Stop at the first refusal you do not understand | A `403` is information. Trying variants to get past it is not testing, it is an attempt to bypass a control |
| Stop if the target shows signs of strain | Rate limits, timeouts and errors are the target telling you to slow down |
| Stop if your contact asks you to | Immediately, and confirm it in writing afterwards |

## What the workbench will not do for you

Stated so that no one relies on a capability that does not exist:

- It will not find a way past an access control. It records the refusal and names
  the authorized route.
- It will not validate a finding. A record marked `POTENTIAL` or `UNVERIFIED` is
  exactly that, and the report says so.
- It will not decide whether your authorization is adequate. It checks the scope
  file's arithmetic, not your authority.
- It will not clean up after a destructive test, because it does not perform one
  without an explicit confirmation at the call site and an authorization that
  permits it.
- It will not protect your evidence from you. Bundles and histories are files; if
  you copy them somewhere, they are there.

## Handling what you collect

- **Treat every bundle as sensitive.** It contains the target's data. Store it
  where the engagement says, and delete it when the engagement ends.
- **Read before you share.** Redaction covers what the tool was told about.
  `docs/workbench/LIMITATIONS.md` says this plainly; believe it.
- **Minimise.** If a proof of access needs one record, do not collect a hundred.
  This is both a legal habit and a practical one: less to store, less to leak,
  less to explain.
- **Keep the chain of custody understandable.** Evidence bundles carry SHA-256
  hashes and a manifest, and `evidence manifest --verify` re-checks them. If you
  hand evidence to someone else, hand them the bundle and the verification
  command, not a screenshot.

## Reporting

- Report the observation, not the conclusion. "The response differed in these
  fields, under these conditions, once" is defensible. "The system is vulnerable"
  is not, unless a person validated it and can reproduce it.
- Say what you did not test. Coverage limits are part of the finding.
- Say what the evidence does not establish, in the words the report uses, rather
  than trimming them for the audience.
- Never inflate severity to get attention. The framework's whole design is a
  refusal to do that; a report that does it anyway has wasted the effort.

## If something goes wrong

1. **Stop.** Cancel the run; the workbench checks for cancellation between
   requests.
2. **Preserve what happened.** History and evidence bundles are append-only and
   hash-verified; do not edit them. If a bundle no longer verifies, say so.
3. **Tell your contact**, promptly, and in writing.
4. **Do not investigate further** on the affected path without instruction. A
   second incident caused while investigating the first is worse than the first.
5. **Record the failure honestly** in the report, including the fact that the
   run's coverage was affected.
