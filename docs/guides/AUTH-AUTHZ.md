# Authentication and Authorization Assessment

## Authentication questions
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

- Can an account be created without required verification?
- Can authentication state be bypassed?
- Are OTP/recovery transitions protected?
- Are sessions bound to the intended user?
- Are tokens properly invalidated?
- Are alternate authentication routes consistent?

## Authorization questions

For each protected operation:

1. Who is the caller?
2. What role do they have?
3. Which object do they access?
4. Who owns the object?
5. What permission should be required?
6. Where is the permission enforced?
7. What happens when an identifier changes?
8. What happens when a role changes?
9. Does the API enforce what the UI expects?

## Horizontal testing

Where multiple authorized test identities exist, determine whether one test identity can access another's protected objects.

## Vertical testing

Where multiple authorized roles exist, determine whether a lower-privileged test identity can invoke higher-privileged operations.

## Conclusions

Use exact statements such as:

- “Cross-user object access confirmed.”
- “Role-bound authorization held for tested operation.”
- “Authorization could not be runtime-tested because no second authorized identity was available.”
