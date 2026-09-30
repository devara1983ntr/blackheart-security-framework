# Legal

**Project:** BLACKHEART Security Framework
**Repository:** `devara1983ntr/blackheart-security-framework`
**Author:** Roshan
**Licence:** MIT (see [`LICENSE`](LICENSE))
**Policy version:** 1.0.0 · **Last updated:** 2026-09-30

---

## Read this first

BLACKHEART is a security research and assessment framework. It contains
documentation, a governed mirror of third-party skills, and a workbench: code
that can send HTTP requests, read files, and record what it observed.

**It does not grant you authorization to test anything.** Possession of it is not
permission. A URL is not permission. A public endpoint is not permission for
security testing beyond ordinary access.

This document is an index. The documents below are the terms. They were written
by the project author and **have not been reviewed by a lawyer**. Where a
statement's effect depends on the law of a particular jurisdiction, the document
says so rather than asserting an outcome.

## Documents

| Document | What it covers |
|---|---|
| [`TERMS-OF-USE.md`](TERMS-OF-USE.md) | The terms you accept by using this repository |
| [`ACCEPTABLE-USE.md`](ACCEPTABLE-USE.md) | Permitted and prohibited uses, explicitly |
| [`SECURITY-RESEARCH-DISCLAIMER.md`](SECURITY-RESEARCH-DISCLAIMER.md) | What this framework is and is not, in plain terms |
| [`PRIVACY-POLICY.md`](PRIVACY-POLICY.md) | What data this project and its code do and do not handle |
| [`AUTHORIZATION-AGREEMENT.md`](AUTHORIZATION-AGREEMENT.md) | A template for recording who authorized what, and for how long |
| [`RESPONSIBLE-USE.md`](RESPONSIBLE-USE.md) | How to use the workbench without causing harm |
| [`THIRD-PARTY-CONTENT.md`](THIRD-PARTY-CONTENT.md) | The vendored catalogue: what it is, whose it is, and how it is treated |
| [`DOWNLOAD-AND-ACQUISITION-POLICY.md`](DOWNLOAD-AND-ACQUISITION-POLICY.md) | The acquisition rules the code enforces |
| [`AI-AGENT-TERMS.md`](AI-AGENT-TERMS.md) | Additional terms when an autonomous agent operates the framework |

The machine-readable form of these rules is
[`policy/BLACKHEART-POLICY.json`](policy/BLACKHEART-POLICY.json).

## What is factually true about this project

Stated here so no other document has to be read charitably:

| Question | Answer |
|---|---|
| Is there a company or legal entity behind this? | **No.** It is an individual's repository. No corporation, partnership, registered address, or legal entity is claimed, because none exists |
| Has a lawyer reviewed these documents? | **No.** Policy version 1.0.0 has had no legal review. `policy/BLACKHEART-POLICY.json` records `"legal_review": "none"` |
| Are there any certifications? | **No.** No ISO, SOC 2, HIPAA, PCI DSS, GDPR, FedRAMP or any other certification or accreditation is claimed |
| Is there a bug bounty? | **No structured programme.** [`SECURITY.md`](SECURITY.md) describes how to report a problem privately |
| Does the framework provide legal protection? | **No.** It is software and documentation. Whether any activity is lawful depends on your authorization, your jurisdiction and your conduct, and that is not something a repository can determine |
| Does the framework collect your data? | The framework does not, and it has no telemetry. [`PRIVACY-POLICY.md`](PRIVACY-POLICY.md) sets out what the platform and your own use of the tool do |
| Are the vendored skills the author's? | **No.** They are third-party content, mirrored and pinned. See [`THIRD-PARTY-CONTENT.md`](THIRD-PARTY-CONTENT.md) |

## The one sentence that matters most

> This framework does not bypass authentication, authorization, paywalls, DRM,
> licensing controls, or other access restrictions.

That sentence appears verbatim in the workbench documentation and as the first
standing statement of every report the workbench generates. It is a description
of what the code does and does not do, and it is enforced by the code rather than
asserted by the prose: see
[`docs/workbench/THREAT-MODEL.md`](docs/workbench/THREAT-MODEL.md).

## Contact

| Purpose | Where |
|---|---|
| Security reports | [`SECURITY.md`](SECURITY.md) — private reporting route |
| Contributions | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Conduct | [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) |

## Changes to these documents

Every document here carries a version. The versions that must agree are recorded
in `policy/BLACKHEART-POLICY.json`, and the workbench records which version an
operator accepted. If these documents change materially, the policy version
increases, the workbench's recorded acceptance stops counting as current, and
`blackheart policy accept` must be run again. This is implemented in
`workbench/policy.py` and tested in `workbench/tests/test_policy.py`; it is not a
statement of intent.
