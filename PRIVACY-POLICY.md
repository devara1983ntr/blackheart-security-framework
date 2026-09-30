# Privacy Policy

**Project:** BLACKHEART Security Framework · **Repository:** `devara1983ntr/blackheart-security-framework`
**Author:** Roshan · **Privacy version:** 1.0.0 · **Last updated:** 2026-09-30

---

## What this document is

A statement of what data this project and its code actually handle. It was
written after auditing the repository, and every factual claim below names the
file or mechanism it comes from, so a reader can check it rather than trust it.

**It has not been reviewed by a lawyer.** Where an obligation depends on your
jurisdiction — data-protection law, retention duties, cross-border transfer —
this document says what the code does and leaves the legal question to you.

## 1. The framework has no telemetry

`workbench/` contains no analytics, no crash reporting, no update check, no
licence check-in and no phone-home of any kind. It opens a network connection for
exactly one purpose: to send a request to a target named in the operator's own
scope file, at the operator's command.

There is no code path that reports usage, errors, counts, versions or identifiers
anywhere. The only socket in the framework is opened in
`workbench/http_client.py`, and every call into it is checked first against the
scope file by `workbench/scope.py`.

## 2. What the workbench stores, and where

Everything below is written to **local storage on the machine running the tool**,
in a location the operator chooses. Nothing is uploaded by the framework.

| What | Where | Contents | Retention |
|---|---|---|---|
| Request history | The file passed to `--history`, JSON Lines | Method, URL, headers (credential values redacted), request body, response status, headers, body, timing, TLS facts, the scope decision | Until the operator deletes the file |
| Evidence bundles | The directory passed to `--out` | Observation records with their hashes, the target, the scope, the reproduction steps and the limitations | Until the operator deletes it |
| Acquisition manifest and downloads | The directory passed to `--out` | Source URL, final URL, HTTP status, content type, size, SHA-256, timestamp, redirect chain, licence note, authorization scope, file type; and the acquired files themselves | Until the operator deletes them |
| Extracted content | The directory passed to `--out` | Text, member listings and page data read from acquired files | Until the operator deletes it |
| Reports | The path passed to `--out` | Derived counts and the records above | Until the operator deletes it |
| Policy acceptance | `~/.blackheart/policy-acceptance.json`, or the directory named by `BLACKHEART_STATE_DIR` | The accepted policy version, a hash of the policy document, and a timestamp. **No identity, no hostname, no user name, no machine identifier** | Until the operator deletes it |

**Records contain the target's data**, because that is what evidence is. A
response body may contain personal data belonging to the target's users. Handling
that is the operator's responsibility, and §6 below sets out what is not the
framework's responsibility.

## 3. Credential material

The workbench redacts, by header name, the values of `Authorization`, `Cookie`,
`Set-Cookie`, `X-API-Key` and `Proxy-Authorization` in everything it writes.
`Set-Cookie` keeps its attributes, because `HttpOnly`, `Secure` and `SameSite`
are evidence a cookie check reads. A value listed with `--secret` is replaced
wherever it appears in a record: request body, response body, URL, query string
and redirect-chain URLs.

What this does **not** cover is stated in
[`docs/workbench/LIMITATIONS.md`](docs/workbench/LIMITATIONS.md): a value the tool
was not told about is not redacted by magic. A randomly generated token in a
response body is stored as received unless it was named with `--secret`. Inspect
a bundle before sharing it.

The workbench never writes credential material to a file of its own, and never
transmits it anywhere except to the target it was supplied for, in the request the
operator asked for.

## 4. Policy acceptance

Acceptance is recorded locally so the tool can tell whether the operator has read
the policy. It records:

- the policy version accepted,
- a SHA-256 of the policy document at the time of acceptance,
- the timestamp.

It does not record who accepted it. It is not uploaded, not synchronised, and not
sent anywhere. Moving the state directory with `BLACKHEART_STATE_DIR` moves the
record; it cannot create one, and a missing record blocks active operations
exactly as an unaccepted policy does.

## 5. The GitHub platform

This repository is hosted on GitHub. When you visit it, GitHub processes data
under its own policies — that is outside this project's control and this document
does not describe it. What this project can state is what its own automation does:

| Automation | Data it handles |
|---|---|
| `validate.yml`, `authored-scan.yml`, `phase5-validation.yml` | Check out the repository's own files on GitHub's runners and run the repository's own gates and tests. They handle no user data and contact no third party |
| `upstream-sync.yml` | Reads two public upstream repositories, compares their commits with the pins in `.github/UPSTREAM-MANIFEST.json`, and opens a pull request for human review |
| `upstream-watch.yml` | Reads the same two public sources, compares commits with the pins, and writes no file. It runs with `contents: read` |
| `site-verify.yml` | Renders the project's own published site in a headless browser and measures it |
| `pages.yml` | Publishes the static site in `site/` to GitHub Pages |
| Dependabot | Reads the repository's dependency manifests. This repository ships no authored runtime manifest; the one Dependabot reads is inside vendored third-party content, and its alerts are recorded as upstream issues to report, not to patch here |

The tests and gates run with **no secrets** and against **a loopback fixture
server** in the repository. No workflow contacts an arbitrary third party, and
none of the test fixtures reach the internet. This is enforced in
`phase5-validation.yml` by restricting the socket layer to loopback for the test
run.

## 6. The published site

`site/` is a static site with no server-side component. Audited at policy version
1.0.0:

| Question | Answer | Evidence |
|---|---|---|
| Analytics or trackers? | **None.** No analytics script, no tag manager, no pixel | No analytics code in `site/*.html`, `site/*.js` |
| Cookies? | **None set.** No `document.cookie` use anywhere | — |
| Third-party embeds? | **None.** No external scripts, stylesheets, fonts or images | Every `src` and `href` in `site/` is a local asset or a link to `github.com` or the project's own Pages URL |
| Local storage? | **One entry**, `bh-theme`, storing the visitor's light/dark theme choice | `site/app.js` |
| Forms? | **None.** The site has no form and no input | — |
| Personal data collected by the site? | **None** | — |

The site links to this project's GitHub repository. Following such a link places
you under GitHub's policies, as does visiting the repository directly.

## 7. Your obligation as an operator

The workbench is built to be used against systems you are authorized to test.
When that testing involves personal data — test accounts, user records, logs
containing identifiers, API responses about people — the data ends up in the
operator's own history, bundles and downloads.

Responsibility for that data is the operator's, and includes:

- the lawful basis for collecting it;
- minimising what is collected to what the engagement requires;
- securing the local files, since they contain target data;
- retention and deletion, including after the engagement;
- responding to any data-subject request that reaches you;
- not transferring it anywhere the engagement does not permit.

The framework provides no facility to help with those obligations beyond writing
everything locally, redacting what it is told to redact, and telling you what it
stored. That limitation is stated plainly rather than papered over.

## 8. Data this project does not process

For completeness, and because a privacy policy that only lists what *is* collected
is easy to misread: this project does not operate a service, does not host user
content, does not maintain user accounts, does not process payments, does not run
analytics on visitors, and does not receive assessment data from the workbench.
There is nothing for it to delete on your behalf, because it never received it.

## 9. Changes

A material change to this policy increases the policy version in
[`policy/BLACKHEART-POLICY.json`](policy/BLACKHEART-POLICY.json), which invalidates
a previously recorded acceptance and requires the operator to accept the policy
again before further active operations. The change is recorded in
[`CHANGELOG.md`](CHANGELOG.md).

## 10. Contact

Security and privacy reports: [`SECURITY.md`](SECURITY.md).
