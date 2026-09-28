# Web and API Security Testing

## Inventory
**Author:** Roshan · **Project:** BLACKHEART Adversarial Security Research Framework

Create a request map for each observed or discovered endpoint:

| ID | Method | Endpoint | Auth | Role | Object | State change | Sensitive data | Evidence |
|---|---|---|---|---|---|---|---|---|

## Core authorization tests

For each object:

- use the legitimate object first;
- identify its ownership model;
- identify the server-side authorization check;
- test authorized vs unauthorized identities when permitted;
- assess direct-object access through alternate requests;
- record exact differences.

## Input integrity

Assess relevant differences among:

- integer vs string;
- `null` vs omitted;
- zero vs positive;
- negative values;
- decimal values;
- duplicate keys;
- duplicate query/body parameters;
- case differences;
- encoding differences;
- alternate HTTP methods.

## API state testing

Where operations mutate state, capture state before and after each request.

Do not call an API response “successful” merely because it returns HTTP 200. Verify the intended state transition.

## Error analysis

Record whether errors reveal:

- SQL/database details;
- internal paths;
- stack traces;
- credentials/tokens;
- object existence;
- payment information;
- internal service identifiers.

Do not disclose unnecessary sensitive details in the final report.
