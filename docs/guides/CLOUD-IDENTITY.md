# Cloud and Identity Assessment

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`AUTH-AUTHZ.md`](AUTH-AUTHZ.md) · [`SCOPE.md`](SCOPE.md) · [`SUPPLY-CHAIN.md`](SUPPLY-CHAIN.md) · [`../modes/RED-HEART-ADVERSARY-EMULATION.md`](../modes/RED-HEART-ADVERSARY-EMULATION.md)

> **Authorized use only.** This guide concerns systems the engagement's
> authorization explicitly covers. **A provider's own infrastructure is never
> in scope** — only the customer's tenancy within it. In a multi-tenant
> provider, the tenant boundary is the security boundary under test; the
> provider's platform is out of scope.

## Why cloud changes the method

In a traditional application the perimeter is the application. In a cloud
environment the effective perimeter is **identity and policy** — a correctly
written application with a misconfigured role can be fully compromised, and a
correctly configured role cannot be helped by any application bug.

This inverts the normal order of work: identity and authorization must be
mapped before application testing, because a broad role can make every
subsequent application finding irrelevant.

## 1. Establish the boundary first

```text
CUSTOMER TENANCY      in scope — the customer's own accounts, resources, data
PROVIDER PLATFORM     out of scope — the provider's own service infrastructure
SHARED SERVICES       out of scope — CDNs, identity providers, payment
                      processors, registries, unless explicitly named
THIRD-PARTY TENANTS   out of scope — other customers, always
```

**The tenant boundary is the highest-value boundary in a multi-tenant
assessment.** Cross-tenant access is the finding that matters most and is
tested with the least rigour. Prioritise it.

## 2. Identity inventory

```text
HUMAN IDENTITIES      users, administrators, service owners, break-glass
NON-HUMAN IDENTITIES  service accounts, roles, workload identities, keys
                       ← routinely the larger and less-reviewed population
FEDERATED             external identity providers, cross-account roles
BREAK-GLASS           emergency access paths, and who can invoke them
```

Non-human identities deserve disproportionate attention. They are numerous,
long-lived, often over-privileged, and rarely reviewed by a human.

## 3. Authorization and policy assessment

```text
POLICY PERMISSIONS    what does each identity actually permit?
BREADTH               is any identity broader than its function requires?
WILDCARDS             do any policies grant action: * on resource: *?
CONDITIONS            are constraints present and correctly evaluated?
DEFAULT AND IMPLICIT  what happens when no policy matches — deny, or allow?
BOUNDARY TRANSITION   which action is allowed solely by being in a trusted
                      network, a source IP, or a VPC endpoint?
CROSS-ACCOUNT         can an identity in one account or project reach another?
```

**The default-deny question is the single most important test.** Many
environments behave as allow-by-default with explicit denies layered on top,
which is invisible until an action is attempted that nobody thought to deny.
Establish the effective default before testing individual permissions.

**Network-boundary conditions deserve scrutiny.** A policy that permits broad
action from a trusted network is a control, but it is a control that an
attacker inside that network inherits entirely. Test whether the network
condition is itself reachable.

## 4. The confused deputy problem

In cloud environments, a service can be induced to act with permissions its
caller does not have. This is the dominant cloud-specific weakness class.

```text
CAN A LOW-PRIVILEGE CALLER cause a HIGH-PRIVILEGE SERVICE to act for them?
  through a parameter the service trusts
  through a resource the service can read but the caller cannot
  through an event or message the service processes as trusted
  through a policy the service evaluates with the wrong identity
```

Where a service reads a resource and passes its contents onward, ask what
stops a caller from supplying a resource they may read but should not be able
to *act* on. This is the pattern behind a large share of real cloud
breaches.

## 5. Storage and data exposure

```text
Bucket / container / share permissions
  Is the resource public when it was not intended to be?
  Does a signed URL outlive the authorization that produced it?
  Is a legitimate read path also a write path?

Encryption
  Is data encrypted at rest, and with keys the customer controls?
  Are keys in scope separately from the data they protect?

Backup and snapshot exposure
  Are backups subject to the same controls as live data?
  How long do they retain access after revocation?
```

A public storage bucket is one of the most common high-severity findings in
cloud assessments and one of the fastest to verify. Check it first.

## 6. Credentials and secrets

```text
Long-lived keys where short-lived credentials are available
Keys shared across environments
Keys present in instance metadata or environment variables
Keys reachable from application code
Rotation process, and whether rotated keys are actually invalidated
```

**Do not use discovered credentials to expand the test.** Finding a
privileged key is a finding to report, not a key to authenticate with and
continue. Use of a discovered credential is active testing against systems
that may not be separately authorized.

The permitted response is to establish the key's scope through the control
plane or through the owner, and to report it. See
[`../templates/ENGAGEMENT-RECORD.md`](../../templates/ENGAGEMENT-RECORD.md).

## 7. Logging and detection

Cloud environments offer strong native audit logging, which is frequently
enabled and frequently unread. The assessment should establish:

```text
Is privileged activity logged?
Is the log retained long enough to detect a slow intrusion?
Are the logs themselves protected from modification?
Would cross-tenant access appear distinguishable from normal activity?
Would bulk data export look different from ordinary reads?
```

An operation that is fully logged but never alerted on provides no detection.
The question is not "is it logged" but "would anyone see it."

## 8. Multi-tenant boundary testing

The defining test of a multi-tenant platform.

```text
Using a low-privilege identity in tenant A:
  [ ] Retrieve an object belonging to tenant B by identifier
  [ ] Enumerate tenant B's resources
  [ ] Reach a tenant B resource via a signed or pre-signed URL
  [ ] Influence a shared service into returning tenant B's data
  [ ] Trigger a notification or webhook carrying tenant B's data
  [ ] Access tenant B through a shared cache, queue, or log
```

**Prove the boundary with one object. Do not enumerate.** Once cross-tenant
retrieval is demonstrated, the finding is established. Continuing is data
collection and is a different, and unacceptable, activity.

Where a shared service caches or fans out responses, test for tenant leakage in
the *delivery* path, not only the storage path. Shared caches, queues, and
notification channels are recurring sources.

## 9. Reporting

```text
FINDING
  Identity or resource
  Effective permissions, as demonstrated
  What the boundary should have enforced
  Whether the default was deny or allow
  Reach: which entry position permits this
  Blast radius: what becomes accessible
  Remediation at the policy layer, per REMEDIATION-AND-RETEST.md
  Regression test
```

Cloud findings are usually policy defects, and the remediation is usually a
narrower policy. State the specific policy change, not "review access".

## 10. Constraints

```text
[ ] Provider platform infrastructure is never tested
[ ] Other tenants' data is never retrieved beyond the minimum that proves
      a boundary failure
[ ] Discovered credentials are reported, not used to expand testing
[ ] No resource is created, modified, or deleted without explicit
      authorization
[ ] No IAM, network, or policy change is made as remediation — the
      assessment recommends; it does not administer
[ ] Cost-incurring resources are not provisioned
[ ] Every untested area is recorded in the coverage matrix
```

## 11. Common failures

| Failure | Correction |
|---|---|
| Testing application code before mapping identity | A broad role makes application findings moot |
| Reporting a policy as safe because it looks restrictive | Establish the effective default |
| Using a discovered credential to continue | Report it; usage is not authorized |
| Enumerating another tenant to prove access | One object proves it |
| Treating provider infrastructure as in scope | The tenancy is in scope; the platform is not |
| Assuming logged means detected | Ask who would see it, and how fast |
| Recommending "review access controls" | State the specific policy change |
