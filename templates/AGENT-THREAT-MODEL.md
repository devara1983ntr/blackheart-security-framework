# AI / Agentic System Threat Model

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../docs/guides/AGENTIC-AI-SECURITY.md`](../docs/guides/AGENTIC-AI-SECURITY.md) · [`../docs/agent/AGENT-SKILL-CATALOGUE.md`](../docs/agent/AGENT-SKILL-CATALOGUE.md)

> Complete before testing. An agentic system is assessed against its **action
> surface**, not its chat interface. This template exists because the most
> common serious omission is a system that was never mapped before it was
> probed.

## 1. System identification

```text
System name:
Purpose, in one sentence:
Model and version:
Orchestrator:
Deployment (hosted / self-hosted / local):
Documentation available: yes / no
```

## 2. Agent inventory

For each agent, record separately. Systems commonly run more agents than their
documentation describes.

```text
AGENT          Name:
               Role / objective:
               Memory:            yes / no — what persists, and for how long
               Retrieval:         yes / no — what index, which tenants
               Tools:             see section 3
               Identity:          what it acts as
               Human oversight:   which actions require approval
```

**Undocumented or shadow agents are themselves a finding.** If one is
discovered during testing and was not declared, record it and report it before
assessing it.

## 3. Tool and action surface

The primary attack surface. One row per tool.

```text
TOOL            Name:
                What it does:
                Parameters accepted:
                Permission scope:
                Acts as identity:
                Action is reversible:      yes / no
                Requires human approval:  yes / no
                Reachable from untrusted input: yes / no
                Needed for the agent's stated purpose: yes / no
```

The last row drives [`../docs/guides/AGENTIC-AI-SECURITY.md`](../docs/guides/AGENTIC-AI-SECURITY.md) §9.
A capability the agent does not need is a least-privilege gap regardless of
whether it has been abused.

## 4. Input channels

Every channel through which untrusted content reaches the model. This is where
indirect injection lives, and it is the section most often left incomplete.

```text
[ ] Direct user input
[ ] Retrieved documents / knowledge base
[ ] Web pages fetched by the agent
[ ] Email or message content
[ ] Tool results — including from trusted tools
[ ] Uploaded files and extracted text
[ ] Inter-agent messages
[ ] API responses from third parties
[ ] Memory written in a previous session
```

For each channel, record: **who can write to it, and who can influence that
writer?**

## 5. Data the system can reach

```text
PRIVATE DATA       what the system can read that a user should not access
SENSITIVE OUTPUT   what the system returns that it should not
RETRIEVAL SCOPE    does retrieval inherit the requesting user's permissions?
                   yes / no / unknown
EXFIL PATH        where can output leave the system, and to whom?
```

## 6. The compound risk

The most serious agentic issue is the simultaneous presence of all three.
Assess explicitly.

```text
Private data reachable:                    yes / no
Untrusted content processed:               yes / no
External exfiltration path:                yes / no
All three present:                         yes / no
```

If all three are present, this is a high-priority compound finding regardless
of whether any individual leg is rated low. It is reported as a combination,
with each leg evidenced separately.

## 7. Trust boundaries

```text
BOUNDARY                     What crosses it            Enforced where
────────────────────────────────────────────────────────────────────
User → model
Model → tool
Model → retrieval index
Tool → external service
Agent → agent
Human → approval gate
```

For each, record **where enforcement actually happens** — not where it is
described. A control that exists only in the system prompt is a request, not a
control.

## 8. Declared vs actual behaviour

```text
What the documentation says the agent will do:
What the agent is observed to do:
Divergence:
```

Divergence between declared and actual behaviour is a finding in itself,
independent of any specific abuse.

## 9. Test plan derived from the model

Derived from this document, not from a generic list.

```text
PRIORITY   Why it is high priority        Layer        Skills
─────────────────────────────────────────────────────────────────
1.         [most damaging credible action] reasoning    G2, G3
2.                                             tool exec   G4, G5
3.                                             retrieval   G6
4.                                             infra       [§3 of guide]
5.                                             inter-agent §12
```

The priority order follows the **worst action the agent could be induced to
take**, not the list of vulnerability categories. A system that cannot move
money is not a payment-security problem regardless of its prompt handling.

## 10. Constraints agreed before testing

```text
[ ] No unbounded request volume or cost testing
[ ] No real external action (send, purchase, delete, post) without explicit
      written authorization for that specific action
[ ] No real personal data placed into prompts or corpora
[ ] No third-party model endpoint stressed
[ ] Planted payloads inert and attributable
[ ] Human-oversight bypass testing agreed with the approver
[ ] Rollback plan for any state change made during testing
[ ] Abort conditions written
```

## 11. Sign-off

```text
[ ] Action surface fully enumerated, including undocumented agents
[ ] Tool permissions recorded per tool
[ ] Every input channel listed
[ ] Compound-risk question answered
[ ] Enforcement points identified per boundary
[ ] Test plan derived from this model
[ ] Constraints agreed and written
```

An unticked box becomes a `NOT TESTED` entry in the coverage matrix, with this
document as the reason.
