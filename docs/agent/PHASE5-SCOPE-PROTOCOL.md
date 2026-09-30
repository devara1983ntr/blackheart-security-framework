# Phase 5 scope protocol

**For:** an AI agent, or a human operating one
**Implementation:** `workbench/scope.py` — this document describes what is there,
and nothing that is not
**Check the file before you trust it:** `python3 -m workbench.cli scope validate --scope scope.json`

---

## 1. What the scope file is

The machine-checked form of an authorization. It names what may be requested, how
much, and until when. Every request passes through `require()`, which **raises**
rather than returning a flag — so there is no branch in the code where a `False`
might be ignored, and no parameter that turns it off.

A scope file is the operator's assertion of an authorization. The tool checks the
assertion's arithmetic and structure. It cannot check its truth.

## 2. The fields

| Field | Type | Default | What it does |
|---|---|---|---|
| `targets` | list of strings | required | The target or targets, for the record and the summary |
| `allowed_hosts` | list of strings | required | Hostnames that may be contacted. A request to any other host is refused |
| `allowed_paths` | list of strings | `[]` | Path prefixes that may be requested. Empty means the host is reachable but no path is restricted by this field |
| `excluded_hosts` | list of strings | `[]` | Hosts that are refused even if otherwise allowed |
| `excluded_paths` | list of strings | `[]` | Path prefixes refused even if otherwise allowed |
| `allowed_methods` | list of strings | required | HTTP methods permitted. Validated against a known set; an unknown method is refused at load |
| `max_requests` | positive integer | **required** | The request budget for the run |
| `max_concurrency` | integer | `1` | Requests in flight. Floored at 1 |
| `max_response_bytes` | integer | `5,000,000` | Bodies are capped on the read, not after |
| `max_redirects` | integer | `5` | Redirect hops, each re-checked against scope |
| `timeout_s` | number | `10.0` | Connect and read timeout |
| `min_interval_s` | number | `1.0` | Minimum spacing between requests |
| `authorized_until` | ISO-8601 date or timestamp, UTC | `None` | When the authorization lapses |
| `allow_private_networks` | boolean | `false` | Whether loopback, private, link-local and reserved addresses may be contacted |
| `notes` | string | `""` | Free text, carried into the record |

**A scope with no positive `max_requests` is refused at load.** An unbounded request
budget is not a scope; the loader says so rather than defaulting one in.

**Fields are validated, not coerced.** An unknown key is a refusal — the loader
names it rather than ignoring it, so a typo in a field name cannot silently do
nothing.

## 3. What is refused, and how it reads

| Situation | Refusal |
|---|---|
| File not found, or not valid JSON | `scope file not found: <path>` / `<path> is not valid JSON: …` |
| Empty file | `<path> is empty: an empty scope authorizes nothing` |
| A key that looks like a control being disabled (`ignore_scope`, `bypass_scope`, `skip_scope_check`, `disable_scope`, `unsafe`, `insecure`) | `scope contains a key that would disable a control (…). There is no bypass: remove it, or do not run this against the target` |
| Any other unknown key | `unknown scope key(s): …` |
| `max_requests` missing, zero or negative | `max_requests must be a positive number: an unbounded request budget is not a scope` |
| A method outside the known set | `invalid HTTP method(s) in allowed_methods: …` |
| A non-boolean `allow_private_networks` | `allow_private_networks must be true or false` |
| A malformed `authorized_until` | `authorized_until is not a valid ISO-8601 date: …` |

**There is no bypass key, no override field and no "trusted" flag.** A file that
tries to invent one fails to load, and the CLI exits `2`.

## 4. Every request, checked in this order

1. **Policy gate.** The policy has been accepted on this machine, and the
   acceptance is current. (First statement of `http_client.request()`.)
2. **Host.** In `allowed_hosts`, not in `excluded_hosts`.
3. **Path.** Inside `allowed_paths` where that list is non-empty, and not inside
   `excluded_paths`.
4. **Method.** In `allowed_methods`. Write methods additionally require explicit
   confirmation at the call site.
5. **Window.** `authorized_until`, if set, has not passed.
6. **Budget.** `requests_made < max_requests`.
7. **Interval.** At least `min_interval_s` since the previous request.
8. **Address.** Every resolved address is checked. Loopback, private, link-local,
   multicast and reserved ranges are refused unless the scope opted in — and the
   opt-in widens the address space, never the host list.
9. **Redirects.** Each hop is re-decided against the same rules. A redirect to an
   off-scope host is recorded as a refusal, per hop.

A failure at any step raises, and **nothing is sent**.

## 5. What an agent must not do with a scope file

| Never | Why |
|---|---|
| Edit the scope file to make a request pass | Editing scope is an authorization decision, and it belongs to whoever granted it |
| Add a host "just for a redirect" | The redirect target is exactly the case the check exists for |
| Raise the budget or lower the interval to finish a run | Those numbers came from the authorization |
| Set `allow_private_networks` to reach an internal address | That flag exists for internal engagements whose authorization says so |
| Retry with a different method, header or encoding after a refusal | A refusal ends that path |
| Write a scope file on the operator's behalf | The assertion must be theirs |
| Read only the summary and assume the limits | `scope validate` prints the enforced values; read them |

## 6. Worked examples

```bash
# What will actually be enforced, before anything is sent
python3 -m workbench.cli scope validate --scope scope.json

# A refused host, refused before any connection
python3 -m workbench.cli http inspect --scope scope.json --url https://not-listed.test/
#   -> exit 3, the refusal names the rule

# A refused budget
#   max_requests: 0   ->  the loader refuses the file, exit 2
```

Exit codes: `0` the command ran, `1` it could not run, `2` usage — including a
malformed or refused scope file — `3` the scope refused a request the command
needed to make.

## 7. Scope in a run, not only at the start

- **Discovery** checks every discovered reference against scope before requesting
  it, and records what it declined to follow. A linked external domain is **not**
  automatically in scope.
- **Fuzzing** spends from the same budget and respects the same interval; the
  budget is a run-wide ceiling, not a per-command allowance.
- **Acquisition** re-checks each redirect hop and records the chain.
- **Emergency mode** uses the same scope with a tighter budget:
  `min(scope.max_requests, 20)`.

## 8. When scope is missing or wrong

| Situation | What the tool does | What the agent does |
|---|---|---|
| No `--scope` on a command that needs it | Exits `2`, names the missing argument | Stops. Does not go looking for another command that sends the same request |
| The scope file does not load | Exits `2` with the loader's reason | Reports the reason verbatim. Does not repair the file |
| The scope does not cover the target | Exits `3` with the decision | Records the decision, names the authorized route, stops that path |
| The scope covers the target but the request is refused by the target | Recorded as `blocked` with the status and the route | Same |

The distinction matters in a report: "the tool refused this because the scope does
not list it" and "the target refused this" are different findings, and dressing one
as the other misrepresents both.
