# Agentic AI Security Testing

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
**Related:** [`../agent/AGENT-SKILL-CATALOGUE.md`](../agent/AGENT-SKILL-CATALOGUE.md) · [`WEB-API-TESTING.md`](WEB-API-TESTING.md) · [`AUTH-AUTHZ.md`](AUTH-AUTHZ.md) · [`REFERENCE-MAPPINGS.md`](REFERENCE-MAPPINGS.md) · [`../SECURITY.md`](../../SECURITY.md)

> **Authorized use only.** This guide grants no authorization to test any
> system, model, or endpoint.

## 1. Why this needs its own method

An LLM-backed application is not an application with a new endpoint. Three
properties break most conventional testing assumptions:

1. **The control plane is natural language.** Security intent lives in a
   prompt, which is a probabilistic instruction rather than an enforced rule. A
   control that exists only in a system prompt is not a control — it is a
   request, and it loses to the right input.
2. **The attack surface includes everything the model reads.** Every
   retrieved document, tool result, and external page is an input channel.
   The user chat box is one of many, and usually the least dangerous.
3. **The system acts.** Where an agent has tools, a successful injection
   becomes an action with real consequences, not a bad sentence.

Conventional testing also has a calibration problem: model output is
probabilistic, so a result that reproduces once may not reproduce again, and a
refusal may be luck. The framework's evidence discipline applies with more
force here, not less.

## 2. Threat model first

Do not begin with payloads. Begin by enumerating the system.

```text
COMPONENTS
  Model(s) and version(s)              :
  System prompt location and content    :
  Memory / conversation store           :
  Retrieval or RAG index                :
  Orchestrator                          :
  Agent(s) and their roles              :

TOOLS — for each
  Name                                  :
  What it does                          :
  Permission scope                      :
  Whose identity does it act as          :
  Is the action reversible               :

EXTERNAL SERVICES
  Third-party APIs called               :
  MCP / tool servers connected          :
  Inter-agent channels                  :

INPUT CHANNELS — every one
  User input                            :
  Retrieved documents                   :
  Tool output                           :
  Web content                           :
  Email / messages                      :
  File uploads                          :
  Inter-agent messages                  :
```

**The tool set is the real attack surface.** A team that maps its chat
interface and stops has missed where the risk actually is. Enumerate G1 in
[`../agent/AGENT-SKILL-CATALOGUE.md`](../agent/AGENT-SKILL-CATALOGUE.md) before
anything else.

## 3. The four layers

Test all four. Most coverage gaps are omitted layers, not omitted payloads.

```text
1. REASONING          prompt injection, goal hijack, instruction priority
2. TOOL EXECUTION     authorization, parameter integrity, sequence control
3. INFRASTRUCTURE     network egress, secrets, storage, third-party calls
4. INTER-AGENT        message authentication, identity, delegation
```

Layer 3 is the one most often skipped entirely, and it is where the
highest-impact findings usually live — because it is where the agent's actual
capability is.

## 4. The critical combination

The most serious issue in an agentic system is not any single weakness. It is
the simultaneous presence of three things:

```text
   PRIVATE DATA          the system can read data the user should not access
        +
   UNTRUSTED CONTENT    it processes input an attacker can influence
        +
   EXTERNAL EXFIL       it can transmit to somewhere the attacker controls
        =
   COMPLETE DATA BREACH  no further exploit required
```

This is a **compound risk**, not a vulnerability with a single identifier. Test
for it explicitly: does an attacker who can influence one input channel
achieve disclosure of data through the third?

Assessing any one of the three in isolation will rate it low. The severity of
the combination is the finding, and it must be reported as such — with all
three legs evidenced, not inferred.

## 5. Prompt injection

### Direct injection
Attacker-controlled text enters through the user channel. Test whether
system instructions can be overridden, deprioritised, or reframed.

Assess against a defined control: what *should* the system refuse to do
regardless of how the request is framed? A response that is merely unhelpful is
not a finding. A control that is bypassed is.

### Indirect injection
The serious case. Content the agent retrieves carries instructions, and the
agent treats retrieved text as command.

```text
Channels to test, each individually:
  Retrieved documents / knowledge base entries
  Web pages the agent fetches
  Email or message content
  Tool results — including results from tools the developer trusts
  Uploaded files and their extracted text
  Inter-agent messages
```

**Labelled-canary method.** Place an inert, unambiguous instruction in a
controlled document — one that would cause a distinctive, harmless observable
action if followed. Then query the agent in a way that would surface the
result. If the observable appears, the retrieved content is being executed as
instruction.

Use a canary, not a destructive payload. The finding is "retrieved content is
treated as instruction", and it is demonstrable without causing harm.

### Single-turn versus multi-turn
Safety behaviour that holds on turn one may not hold on turn ten. Test both
and report them separately — a system that resists a single-turn injection and
yields to a gradual multi-turn reframing is a real and under-reported finding.

## 6. Tool execution

The highest-value area, and the one that produces real impact.

```text
SEQUENCE      can the agent be induced to call tools out of order, or skip a
              step the design requires?
PARAMETERS    can arguments be manipulated to act on something other than
              what the user asked for?
TARGET        can a tool be pointed at a different resource, tenant, or user?
COMBINATION   can individually-safe permissions be chained into a capability
              beyond their intent?  ← the privilege-escalation pattern
CONFIRMATION  are high-impact actions gated on human approval, and can that
              gate be bypassed or socially engineered?
```

**Test authorization at the tool layer, independently of the model.** Send a
crafted tool invocation directly to the tool's own access-control surface,
without going through the model at all. If the tool accepts it, the tool is
unprotected regardless of what the prompt says. This is a fast, deterministic
test that produces binary evidence — prefer it over model-mediated probing
whenever it is available.

## 7. Retrieval and RAG

Retrieval is a second input channel with its own authorization surface. It does
not automatically inherit the requesting user's permissions.

```text
Direct cross-tenant    as identity A, query content scoped to identity B
Induced disclosure     influence retrieved content to cause the agent to
                       emit another tenant's content
Scope propagation      does a document the user may read cause the agent to
                       retrieve one they may not?
Injection in corpus    does a retrievable document reach a tool call?
```

The last is the compound risk from §4 in its RAG instance: content planted in
the corpus that flows into a tool invocation.

## 8. Memory and persistence

Where the agent retains state across sessions:

```text
1. Plant attributable content in session 1
2. Close the session
3. Open a new session
4. Test whether the planted content changes behaviour
```

Persistence is only `CONFIRMED` when behaviour demonstrably changes in a later
session. A stored string is not persistence; a behaviour change is.

## 9. Excessive agency

Assess three properties separately, because the fix differs for each:

| Property | Question | Typical fix |
|---|---|---|
| **Functionality** | Does the agent hold capabilities it does not need? | Remove the tool |
| **Permissions** | Does each capability exceed what its task requires? | Narrow scope |
| **Autonomy** | Can it act irreversibly without approval? | Require human confirmation |

A read-only assistant holding write access is a permissions finding. An agent
that can act irreversibly without confirmation is an autonomy finding. They
need different fixes, so they must be reported separately.

## 10. System prompt and configuration exposure

Test whether the system prompt, internal configuration, or tool definitions
can be extracted. Treat what is retrieved as evidence.

**If a credential or live secret is recovered:** do not publish it. Redact it,
preserve enough to prove the exposure, and report it as a secret-exposure
finding with the rotation requirement stated. This is the framework's existing
secret-handling rule applied to a new context.

## 11. Output handling

Assess what happens *after* the model speaks. Output rendered as HTML, passed
to an interpreter, used in a shell command, or inserted into a downstream
query is an injection sink.

```text
Is output escaped before rendering?
Is output ever treated as executable?
Does downstream code validate before using model output?
```

A model that will emit attacker-chosen text is not itself a finding. A system
that executes that text is.

## 12. Agentic-specific boundaries

Where multiple agents or an external tool protocol are present:

```text
IDENTITY        can one agent assume another's identity in the mesh?
MESSAGE TRUST   are inter-agent messages authenticated, or merely accepted?
DELEGATION      can a delegation chain carry privilege the origin did not have?
TOOL PROVENANCE is tool output distinguishable from instruction?
COLLISION       can a tool be registered under a name that resolves to a
                different, more privileged capability?
FAILURE         does one agent's failure or compromise propagate downstream?
```

Unauthenticated inter-agent messaging is a real finding, not a hardening
suggestion.

## 13. Mapping to OWASP

### OWASP Top 10 for LLM Applications (2025)

| ID | Risk | BLACKHEART skill |
|---|---|---|
| LLM01 | Prompt Injection | G2, G3 |
| LLM02 | Sensitive Information Disclosure | G3, G6, §10 |
| LLM03 | Supply Chain | See [`SUPPLY-CHAIN.md`](SUPPLY-CHAIN.md) |
| LLM04 | Data and Model Poisoning | G7, §11 |
| LLM05 | Improper Output Handling | G8, §11 |
| LLM06 | Excessive Agency | G4, G5, §9 |
| LLM07 | System Prompt Leakage | §10 |
| LLM08 | Vector and Embedding Weaknesses | G6, §7 |
| LLM09 | Misinformation | Output verification, §11 |
| LLM10 | Unbounded Consumption | G9, §14 |

### Agentic risk categories

| Risk | Question |
|---|---|
| Agent goal hijack | Can the agent's objective be redirected mid-task? |
| Tool misuse | Can the agent be coerced into calling tools beyond its intent? |
| Identity and privilege abuse | Can the agent act with borrowed or over-broad credentials? |
| Agentic supply chain compromise | Can a tool, plugin, or connected server be poisoned? |
| Unexpected code execution | Does agent-generated or agent-triggered code run privileged? |
| Memory and context poisoning | Does attacker state persist and bias future sessions? |
| Insecure inter-agent communication | Are agent messages authenticated? |
| Cascading failures | Does one compromised agent corrupt others? |
| Human-agent trust exploitation | Can approval be socially engineered? |
| Rogue agents | Are agents operating outside monitoring or governance? |

> **Verify before citing.** These taxonomies move between versions. Confirm the
> current identifiers and definitions before using them in a client deliverable,
> and state the version you mapped against.

## 14. Coverage and reporting

Agentic testing is frequently reported as a set of prompts that "did not work".
That is not a result.

```text
Layers tested            : reasoning / tool execution / infrastructure / inter-agent
Input channels tested    : list each, with status
Tools enumerated         : N of N; permissions recorded
Single-turn tested       : yes / no
Multi-turn tested        : yes / no
Retrieval path tested    : yes / no / not present
Memory persistence tested: yes / no / not present
Corpus size / sample     :
Repeatability            : how many runs, how many reproduced
```

**Repeatability is mandatory** for probabilistic results. State the number of
runs and the reproduction rate. "Reproduced once" and "reproduced in 20 of 25
runs" are different findings with different severities, and the difference
matters to whoever has to fix it.

Report untested layers explicitly. An untested layer in an agentic engagement
is a coverage gap, and per the framework's rules it is a gap — not an absence
of findings.

## 15. Non-negotiable constraints

```text
[ ] No unbounded request volume or cost testing — ever
[ ] No test that causes a real external action (send, purchase, delete,
    post) without explicit written authorization for that action
[ ] No real personal data placed into prompts or corpora for testing
[ ] No third-party model endpoint stress-tested
[ ] Planted payloads are inert and attributable
[ ] Retrieved secrets redacted, not published
[ ] Coverage gaps stated, not omitted
```

The first is absolute. The others are absolute whenever authorization has not
explicitly covered them.
