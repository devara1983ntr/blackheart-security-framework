# Decision Matrix

**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Maps an observed situation to the correct [evidence status](../../AGENT.md#5-evidence-status-taxonomy)
and bounds the conclusion that may be drawn from it.

## Status mapping

| Situation | Correct status | Required conclusion |
|---|---|---|
| Suspicious code only | UNVERIFIED | Explain hypothesis and missing proof |
| Configuration weakness only | UNVERIFIED or informational | Explain what runtime proof is missing |
| Manipulated request accepted | CONFIRMED for the input-integrity weakness | Do not automatically claim downstream impact |
| Payment amount changed | CONFIRMED price/payment-integrity issue | Payment bypass only if payment requirement was actually bypassed |
| Payment state accepted incorrectly | CONFIRMED payment-verification weakness | Entitlement still separate |
| Premium entitlement granted without required condition | CONFIRMED entitlement bypass | Continue to verify protected functionality/delivery |
| Premium feature usable without required entitlement | CONFIRMED premium-access bypass | Determine scope of actual functionality |
| Protected file delivered without required authorization | CONFIRMED download bypass | Preserve and validate actual file where permitted |
| Actual protected artifact acquired | CONFIRMED actual acquisition | Record real file metadata/hash and evidence |
| Test not possible | NOT TESTED | State exact blocking capability |
| Third-party asset not authorized | OUT OF SCOPE | Record dependency without active testing |
| Control held under tested conditions | NOT VULNERABLE | State exact coverage; avoid universal claims |

## Severity is a separate axis

Status answers *what the evidence proves*. It does not answer *how bad it is*.
For the severity rubric, including the rule that an unproven finding cannot be
rated above its evidence, see [`SEVERITY-RATING.md`](SEVERITY-RATING.md).

## Worked examples

**Price field accepts a client-supplied amount**

```text
Status   : CONFIRMED  — input-integrity / price-integrity weakness
Severity : rate the demonstrated effect on order amount, not the theoretical
           ceiling of "free products"
Not      : "payment bypass"  ← requires proof the payment requirement was
           actually bypassed, which is a separate claim
```

**Signed download URL still valid after entitlement removal**

```text
Status   : CONFIRMED  — download authorization does not track entitlement state
Severity : rate the staleness window and the artifact's value
Not      : "payment bypass"  ← no payment condition was involved
```

**Client-side premium check present, server response not yet observed**

```text
Status   : UNVERIFIED  — client-side control is a hypothesis until the server
           behaviour is observed
Severity : do not rate. Unverified items are not severity-rated; they are
           listed with the exact missing proof.
```
