# Command surface

One command per capability. `--json` is available on every command and prints a
single object on stdout; without it, the human-readable lines go to stdout.

Invoke as `python3 -m workbench.cli <group> <command> [options]`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | The command ran and produced its output. This says nothing about whether the target looked healthy: a scan that recorded six observations exits `0`, and so does a download that was refused with `403`. |
| `1` | The command could not run, or could not produce its output — a file it was given is unreadable, a manifest did not verify, a description was not in a format it can read. |
| `2` | The arguments were wrong: a required `--scope` was not given, a scope file was refused as malformed, a target was outside the scope, a `--header` was not `Name: value`. |
| `3` | The scope file refused a request that the command needed to make. |

A program reading the output should branch on the exit code and then on the
payload, which always carries a `status` field of `ok` or `failed`.

## Flags that appear on every command that sends a request

| Flag | What it does |
|---|---|
| `--scope FILE` | Required. The authorization file every request is checked against. There is no default and no flag that skips it. |
| `--secret VALUE` | Repeatable. A value to redact from everything recorded: request and response bodies, the URL, the query string and every URL in a redirect chain. A record whose URL was redacted cannot be replayed or fuzzed — the tool refuses rather than sending the marker. |
| `--json` | One JSON object on stdout, with the human-readable lines on stderr. |
| `--history FILE` | Append every exchange to this file as JSON Lines, for `http diff`, `http mutate`, `http replay` and `http fuzz`. |

`api inspect` also accepts `--scope` (it can fetch the description) but does not
require it, because `--file` reads a local document and sends nothing.

## Commands

`--scope` is **required** where a command sends a request, **optional** only for
`api inspect` (which can read a local file), and absent where a command reads
local files only.

| Command | Scope | What it does |
|---|---|---|
| `scope validate --scope FILE` | — | Checks a scope file and prints the summary that will be enforced. |
| `http inspect --scope FILE --url URL [--method M] [--header 'N: v'] [--history F]` | required | One request, in full: status, final URL, redirect chain, headers, size, timing, the scope decision. |
| `http replay --scope FILE --history F --id ID [--method M] [--header] [--body] [--confirm-write]` | required | Re-sends a stored request as a new record, linked to the original, and reports how the response differs. A write method needs `--confirm-write` and a scope that allows it. |
| `http diff --history F --from ID --to ID` | — | Compares two stored exchanges and describes the observable differences. |
| `http mutate --history F --id ID [--kinds LIST] [--apply N]` | — | Lists the mutations that could be made to a stored request. Sends nothing; `--apply N` prints the request it would send. |
| `http fuzz --scope FILE --history F --id ID [--kinds] [--limit N] [--budget N] [--confirm-write]` | required | Sends mutations within a limit and a budget, records every result, and stops on cancellation. |
| `api discover --scope FILE --url URL [--max-pages N] [--max-depth N] [--budget N]` | required | Looks for API descriptions at conventional locations and lists the operations they declare. Calls nothing it finds. |
| `api inspect (--url URL \| --file PATH)` | optional | Reads one JSON API description and lists its operations, marking the ones that declare a write and those that declare authentication. |
| `web crawl --scope FILE --url URL [--max-pages N] [--max-depth N] [--budget N] [--no-assets]` | required | Discovery within the scope: published paths, links, forms, script references, API documents. |
| `web scan --scope FILE --url URL [--extra-url U] [--out DIR]` | required | Requests the given URLs and runs the observable checks, writing an evidence bundle. |
| `resource inspect --path PATH [--max-bytes N] [--max-depth N] [--quarantine DIR]` | — | Reads a local document, archive or file and reports what it is, without executing or extracting anything outside the limits. |
| `resource download --scope FILE --url URL [--out DIR] [--expect document\|page] [--sha256 H] [--license NOTE] [--yes]` | required | Acquires one resource, with provenance, and records the outcome in `downloads/manifest.json` whether it succeeded or was refused. Plans and sends nothing until `--yes`. |
| `resource extract --manifest FILE [--id ID] [--out DIR]` | — | Reads the files a manifest records as successfully obtained, within the extraction limits, and updates each entry's extraction status. |
| `evidence hash PATH...` | — | SHA-256 of files on disk. |
| `evidence manifest --directory DIR [--out FILE] [--verify]` | — | Indexes a directory of records, or re-hashes a bundle or download manifest and reports what disagrees. It will not overwrite an existing manifest unless `--out` names a different file. |
| `emergency collect --scope FILE --url URL [--out DIR] [--budget N] [--yes]` | required | Read-only collection: the target URL, `/robots.txt` and `/.well-known/security.txt`. Plans and sends nothing until `--yes`. |
| `report generate [--bundle DIR] [--manifest FILE] [--scope FILE] --out FILE [--title T] [--note N]` | optional | Writes a report from the records a run produced. Every count in it is derived from those records. |

## Examples

```bash
# Authorise a target, then check the file before anything uses it.
python3 -m workbench.cli scope validate --scope scope.json

# Record a request and its response.
python3 -m workbench.cli http inspect --scope scope.json \
    --url https://target.example/ --history run/history.jsonl

# See what could be varied on that request, without sending anything.
python3 -m workbench.cli http mutate --history run/history.jsonl --id H0001

# Send at most 25 mutations, spaced by the scope's interval.
python3 -m workbench.cli http fuzz --scope scope.json \
    --history run/history.jsonl --id H0001 --limit 25 --budget 30

# What the target publishes about itself.
python3 -m workbench.cli web crawl --scope scope.json \
    --url https://target.example/ --max-pages 25 --max-depth 2

# Acquire one published document. Without --yes this prints the plan.
python3 -m workbench.cli resource download --scope scope.json \
    --url https://target.example/report.pdf --out run/downloads \
    --license "public domain, per the publisher's page" --yes

# Read what was obtained, and record what each archive contained.
python3 -m workbench.cli resource extract \
    --manifest run/downloads/manifest.json --out run/extracted

# Check the bundle hashes before writing a report over them.
python3 -m workbench.cli evidence manifest --directory run/evidence --verify

# Write the report.
python3 -m workbench.cli report generate --bundle run/evidence \
    --manifest run/downloads/manifest.json --scope scope.json \
    --out run/report.md
```

## Deliberate refusals in the surface

These are not bugs to work around:

- `http replay` of a write method without `--confirm-write` exits `3`.
- A target outside `allowed_hosts`, an excluded path, a method that is not
  allowed, or an exhausted budget exits `3`, and nothing was requested.
- `resource download` of a resource behind a `401`, `402`, `403`, `407`, `451` or
  a challenge page does not fail: it records `blocked`, writes no file, and exits
  `0` with the authorised route in the output.
- `evidence manifest` refuses to overwrite a manifest that is already in the
  directory, because the file it would replace is the record of a run.
- `report generate` over a bundle whose hashes no longer match produces the
  report and states the problem in it, rather than refusing or ignoring it.
