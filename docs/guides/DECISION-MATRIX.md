# Decision Matrix

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
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework
