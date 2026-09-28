# Security Policy & Responsible Use

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Maintainer:** Roshan — <https://github.com/devara1983ntr>

## Supported versions

This repository is a **documentation and methodology project**. It ships no
software releases, no binaries, and no deployable code. There is no version to
patch.

| Scope | Supported |
|---|---|
| Current `main` branch | Documentation changes reviewed on pull request |
| Historical commits | Not maintained |

## Reporting a documentation or methodology defect

If you find an error, ambiguity, or a methodological flaw in this
documentation that could lead a practitioner to an incorrect or unsafe
conclusion, please open an issue describing:

- the document and section
- what the document currently says
- why that is incorrect or unsafe
- what it should say instead

**Security-relevant documentation defects are prioritised** over typos and
formatting issues.

### Do not open a public issue for

- exploitation of third-party systems (see below — this is illegal, not a
  disclosure)
- leaked credentials, tokens, or API keys belonging to any party
- personally identifiable information
- vulnerabilities in systems not owned by you

Report those privately to the maintainer instead, and do not include live
secrets in an issue body.

---

## Responsible use policy

> **This repository grants no authorization to test any system.**

The methodology in this repository is intended exclusively for:

- systems you own
- systems you have written permission to test
- systems hosted in an explicitly authorized lab, staging, or sandbox
  environment
- defensive review of your own infrastructure

### What is out of bounds

Do **not** use this methodology against:

- any system you do not own or have written permission to test
- third-party SaaS, CDN, payment-provider, or cloud infrastructure
- other customers' or tenants' data
- production systems outside an explicit authorization agreement
- any system in a way that causes financial loss, data loss, or service
  degradation

A public endpoint, a shared link, a hosting tenancy, or a name similarity does
**not** constitute authorization.

### Rules this framework enforces on itself

These are not optional and apply to any assessment run under this methodology:

1. **Authorization is established before testing begins.** Discovery material
   alone is not authorization.
2. **Third-party dependencies are identified and documented, not attacked.**
   A vendor endpoint found in client code is out of scope unless separately
   authorized.
3. **No fabricated evidence.** No invented hashes, transactions, responses,
   screenshots, artifacts, or exploitation results. A report with unverified
   areas is preferable to a report with fabricated ones.
4. **Minimum necessary data.** Prove the authorization failure with the
   smallest sufficient proof. Do not harvest real user data to demonstrate a
   flaw.
5. **Assessment only.** No remediation, no configuration changes, no data
   modification without explicit instruction.
6. **Negative results are recorded.** A correctly-rejected attack is evidence
   of a control, and is reported.
7. **Impact is proven, not inflated.** Confirm by demonstrated capability, not
   by theoretical possibility.

### Prohibited in all authorized engagements

- credential theft or brute force
- phishing of users or administrators
- session or token theft
- denial-of-service or stress testing
- real payments or deliberate financial loss
- bulk extraction of personal data
- destructive modification of production data
- testing third-party infrastructure that is not itself in scope

---

## Third-party skills

Executable skills under [`skills/third-party/claude-skills/`](skills/third-party/claude-skills/)
are third-party code — 388 skills, 693 scripts. They are vendored
**unmodified** from a pinned upstream commit under MIT, audited before
inclusion, and attributed in [`skills/VENDOR.md`](skills/VENDOR.md). Integrity
is enforced continuously: `.github/UPSTREAM-MANIFEST.json` records a SHA-256 per
skill, and CI fails if any vendored byte changes.

Every skill carries a `_BLACKHEART-ADAPTER.md` recording its audit verdict and
its conditions of use. **A skill without an adapter is unaudited and must not
be used in an engagement**; the validator fails the build if one appears.

They are not a security boundary, and neither is the skill allowlist. An agent
able to execute a shell can reach anything on the host regardless of which
skills it can see. Constrain execution with sandboxing, OS-level isolation, and
per-resource credentials — not with skill visibility.

`skills/catalog/` records a third-party catalogue that was deliberately **not**
integrated. See [`skills/catalog/README.md`](skills/catalog/README.md) for the
reason and the required process for adopting an individual entry.

### Reporting a vulnerability in a vendored skill

Report it to the **upstream author**, not only here. A vulnerability in vendored
code is upstream's to fix, and this repository only pins a commit. Include the
pinned commit in the report.

### Known issues in vendored content

Defects in vendored files are **recorded, not silently patched**, so the mirror
stays comparable to upstream and any local change shows up as a divergence.
The current list — unresolved upstream links, duplicated skill names, and one
sample codebase that must never be executed — is in
[`skills/VENDOR.md`](skills/VENDOR.md) §4.

## Secrets

This repository must never contain credentials, API keys, tokens, session
cookies, or private keys.

If you believe a secret has been committed here, report it privately to the
maintainer. **Do not open a public issue containing the secret**, and do not
attempt to use it to validate that it is live. The correct response is to
report and rotate, not to test.

Maintainers: if a secret is found, revoke it first, then remove it from the
working tree, then purge it from history. Removal from history does not
un-expose an already-published secret — **rotation is the actual fix.**

---

## License

Documentation content is licensed under the [MIT License](LICENSE).
Third-party material, if any, retains its original license.
