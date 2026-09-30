# Terms of Use

**Project:** BLACKHEART Security Framework · **Repository:** `devara1983ntr/blackheart-security-framework`
**Author:** Roshan · **Terms version:** 1.0.0 · **Last updated:** 2026-09-30

---

## 1. What these terms are

These terms apply to your use of this repository: its documentation, its vendored
third-party content, and the workbench code in `workbench/`.

They were written by the project author. **They have not been reviewed by a
lawyer.** Their effect depends on the law where you are, which this document does
not attempt to determine. If you need a legal opinion on your use of this
software, obtain one.

## 2. Who may use it

You may use this framework if, and only if:

1. you will use it only on systems you own or operate, or on systems for which
   you hold authorization from a person or entity entitled to grant it;
2. you will comply with the law that applies to you, and with any additional
   obligation that applies to the target (an engagement contract, a bug-bounty
   policy, a service's terms, an employer policy, an export-control rule);
3. you accept these terms and the documents they reference; and
4. you are legally able to accept them.

If any of those is not true, do not use it.

## 3. Authorization is yours to obtain

**This framework does not grant authorization, and no part of it can.**

- Possessing the source code is not authorization.
- Cloning, forking or installing it is not authorization.
- Being able to reach a URL is not authorization.
- A public, unauthenticated endpoint is not authorization to test it beyond the
  access the operator of that endpoint intends to offer.
- A target you are employed to work on is not automatically in scope; your
  authorization determines scope, not your employment.
- A person's claim of ownership is not, by itself, proof that they may authorize
  testing.

You are responsible for obtaining, understanding and staying inside the
authorization that applies to your activity. The
[`AUTHORIZATION-AGREEMENT.md`](AUTHORIZATION-AGREEMENT.md) template exists to help
you record that authorization; filling it in does not create any authority you did
not already have.

## 4. Scope is a technical limit and a legal one

The workbench requires an authorization scope file on every command that sends a
request, and refuses requests outside it. That mechanism protects against
mistakes. **It is not a legal boundary.** A scope file cannot make testing lawful,
and editing one cannot acquire authority you do not hold. Writing your own scope
file is you asserting authority; the tool checks the arithmetic, not the
authority.

## 5. Lawful use

You are responsible for compliance with the law that applies to you. Which law
applies, and what it permits, depends on where you are and where the target is,
and this document does not attempt to answer that. Common categories of
obligation that may apply include: computer-misuse and unauthorized-access law;
privacy and data-protection law; laws governing interception and monitoring;
intellectual-property and licensing law; contractual terms imposed by the target
or your employer; and export-control rules on security tooling.

Obtain your own advice. Do not treat this repository as legal advice, and do not
treat its statements about what the code does as statements about what you may
lawfully do with it.

## 6. Third-party targets and third-party content

If your testing touches infrastructure operated by someone else, you need that
operator's authorization, and possibly the authorization of others in the chain
(hosting provider, payment processor, third-party API). The framework's scope file
records what you asserted; it does not verify it.

The vendored skills are third-party content under their own licences. See
[`THIRD-PARTY-CONTENT.md`](THIRD-PARTY-CONTENT.md).

## 7. Rate limits, availability and care

You will:

- respect the request budget, rate interval, page, depth and size limits the
  workbench enforces, and not raise them beyond what your authorization permits;
- not run testing that could degrade a target's availability without explicit
  authorization for that specific risk;
- stop when a target shows signs of strain, and stop on cancellation;
- avoid testing production systems in ways that are destructive or that alter
  data, unless the authorization says so explicitly and in writing.

## 8. Data, evidence and downloads

- **Data you collect** during an assessment is your responsibility: its lawful
  basis, its storage, its retention, its transfer and its destruction.
- **Evidence** the workbench writes is stored locally and is not transmitted
  anywhere by the framework. It may contain target data. Treat it as you would
  any other engagement data.
- **Downloads** are governed by
  [`DOWNLOAD-AND-ACQUISITION-POLICY.md`](DOWNLOAD-AND-ACQUISITION-POLICY.md): the
  code will not circumvent an access control, and a blocked resource is recorded
  as blocked.
- **Credential material** you supply is redacted from what the workbench writes,
  as described in [`PRIVACY-POLICY.md`](PRIVACY-POLICY.md) and
  [`docs/workbench/LIMITATIONS.md`](docs/workbench/LIMITATIONS.md). Redaction is
  not a substitute for care: inspect anything you share.

## 9. Prohibited use

The prohibited categories are set out in
[`ACCEPTABLE-USE.md`](ACCEPTABLE-USE.md) and are part of these terms. In summary,
using this framework to access systems, data, accounts, credentials or content you
are not authorized to access; to circumvent any access control, paywall, DRM,
licensing control, rate limit or CAPTCHA; to attack, disrupt or surveil; to deploy
malware; or to fabricate results — is prohibited, and is not a use this project
permits or supports.

## 10. No warranty

The framework is provided **as is**, without warranty of any kind, express or
implied, including any warranty of merchantability, fitness for a particular
purpose, or non-infringement. It may contain defects. It may be wrong about what
it observed. It makes no promise of accuracy, completeness or availability.

## 11. Responsibility and liability

The framework is provided subject to the applicable terms and disclaimers. Users
remain responsible for their use of the framework, their authorization, their
targets, and compliance with applicable law.

To the extent permitted by the law that applies to you, the author and
contributors are not liable for any claim, loss, damage or expense arising from
your use of the framework, including from your testing of any target, from data
you collected, or from a decision you took on the strength of its output. This is
a statement about allocation of responsibility between you and the author; it is
not a claim that liability is excluded in every circumstance, and it cannot
affect any liability that the law does not permit to be excluded or limited. If
that distinction matters to you, take legal advice.

## 12. Output is not a finding

The workbench reports observations. An *observable response difference* is not a
vulnerability. A record marked `POTENTIAL` or `UNVERIFIED` has not been validated.
Reporting such a record as a confirmed defect is prohibited, and is also the
behaviour this framework exists to prevent. See
[`docs/workbench/LIMITATIONS.md`](docs/workbench/LIMITATIONS.md).

## 13. Changes

These terms may change. Each document carries a version; the versions that must
agree are recorded in [`policy/BLACKHEART-POLICY.json`](policy/BLACKHEART-POLICY.json).
A material change increases the policy version, invalidates a previously recorded
acceptance in the workbench, and requires re-acceptance before active operations.
Continuing to use the framework after a change means you accept the changed terms.

## 14. If you do not accept these terms

Do not use the framework. Some of it you may still read — the documentation is
public — but the terms above govern use, and the workbench refuses to send any
request until the policy has been accepted on the machine running it.
