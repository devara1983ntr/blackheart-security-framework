# Digital File Validation and Real Artifact Evidence

## Purpose
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

When an authorized security test obtains a protected digital artifact, validate the actual file rather than using a placeholder.

## Required metadata

Record:

- filename;
- extension;
- MIME/content type;
- byte size;
- SHA-256;
- acquisition timestamp;
- endpoint/path;
- authorization context;
- payment state;
- entitlement state;
- download state.

## Integrity checks

Where appropriate:

- open the file with a parser or relevant application;
- verify archive integrity;
- inspect basic metadata;
- confirm the file type matches the expected type;
- compare size/type to the legitimate product where an authorized baseline exists.

## Artifact evidence block

```text
ARTIFACT STATUS: CONFIRMED / NOT CONFIRMED
FILENAME:
TYPE:
SIZE:
SHA-256:
ACQUIRED AT:
ENDPOINT:
ACTOR/ROLE:
PAYMENT STATE:
ENTITLEMENT STATE:
EXPECTED ACCESS CONDITION:
OBSERVED ACCESS CONDITION:
VALIDATION RESULT:
```

## Attachment rule

If the actual downloaded artifact exists and the assessment environment permits attachment, attach the real artifact. Do not create a synthetic file and label it as evidence.

## Privacy rule

Do not redistribute personal or sensitive user content merely because it was exposed. Preserve only what is necessary for the security finding and follow the engagement's evidence-handling rules.
