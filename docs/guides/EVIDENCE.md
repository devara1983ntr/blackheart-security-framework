# Evidence Handling

## Evidence hierarchy
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Prefer, in order:

1. direct server responses;
2. actual state changes;
3. actual protected-resource access;
4. actual downloaded artifacts;
5. reproducible request sequences;
6. application/source evidence;
7. configuration evidence;
8. screenshots/logs supporting the above.

## Minimum evidence principle

Collect enough evidence to prove the security property and no more than necessary.

## Cryptographic hashes

For actual downloaded files, compute SHA-256 from the exact artifact submitted as evidence.

Never manually invent or estimate hashes.

## Evidence naming convention

Suggested structure:

```text
EVIDENCE/
  FINDING-001/
    request-001.txt
    response-001.txt
    request-002.txt
    response-002.txt
    screenshot-001.png
    artifact.zip
    artifact.sha256
    metadata.txt
```

## Evidence linkage

Every finding should identify the evidence files used to support it.

## Redaction

Redact credentials, tokens, secrets, and unnecessary personal data before the final report while retaining enough context to prove the issue.
