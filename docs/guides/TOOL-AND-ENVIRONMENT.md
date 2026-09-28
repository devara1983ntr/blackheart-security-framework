# Tool and Environment Rules

## Capability discovery
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

At the beginning of the assessment, report what is actually available.

## Tool-use honesty

Never claim to have used a tool that was not available or was not actually executed.

## Substitution

When a preferred tool is missing, use a technically equivalent available method when practical.

Examples:

- preferred intercepting proxy unavailable → controlled HTTP capture/replay method;
- Android runtime unavailable → static APK analysis;
- JADX unavailable → other available DEX/static inspection;
- browser automation unavailable → direct HTTP analysis where sufficient.

The substitution must be stated in the methodology section.

## Runtime limitations

Static analysis cannot prove runtime behavior unless the evidence directly establishes it.

A lack of an exploit under one environment does not automatically establish universal security.

## Reproducibility

Record:

- environment;
- tool versions where relevant;
- target version/hash;
- test identity;
- date/time;
- important configuration.
