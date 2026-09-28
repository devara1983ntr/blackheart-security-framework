# Payment, Premium, Entitlement and Digital-Product Testing

## Objective
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Determine whether an authorized target incorrectly grants paid access, premium functionality, entitlement, or digital-product delivery when the intended payment/authorization condition has not actually been satisfied.

## State model

```text
PRODUCT_SELECTED
    ↓
PRICE_COMPUTED
    ↓
ORDER_CREATED
    ↓
PAYMENT_STARTED
    ↓
PAYMENT_AUTHORIZED/CAPTURED
    ↓
PAYMENT_VERIFIED
    ↓
ENTITLEMENT_GRANTED
    ↓
PREMIUM_ACCESS_ENABLED
    ↓
DOWNLOAD_AUTHORIZED
    ↓
FILE_DELIVERED
```

## Test dimensions

### Price integrity

Investigate relevant client-controlled values, including numeric/string representation, discounts, quantities, currency, rounding, zero/negative handling, duplicate parameters, and product substitution.

### Order integrity

Check whether order identity, product identity, user identity, amount, and currency remain bound together.

### Payment integrity

Assess whether server-side verification uses authentic payment-provider evidence and correct transaction/order/product/user bindings.

### Replay and state confusion

Investigate whether successful, failed, abandoned, refunded, or cancelled states can be replayed or substituted.

### Entitlement integrity

Determine exactly what server-side condition creates the entitlement and whether that condition can be reached through an alternate workflow.

### Premium-feature controls

Determine whether premium functionality is protected server-side or only hidden/disabled in the client.

### Download authorization

Test whether the file-delivery layer independently checks entitlement and whether links can be reused, substituted, or accessed through alternate paths.

## Conclusion rules

Do not write “payment bypass” unless the required payment condition was not fulfilled and the system nevertheless accepted the purchase as valid for protected access.

Do not write “premium download bypass” unless the protected file was actually delivered or equivalent protected access was conclusively demonstrated.

A lower-value intermediate issue must be reported separately when the full impact chain remains unverified.
