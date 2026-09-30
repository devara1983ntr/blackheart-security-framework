"""BLACKHEART Phase 5 — the authorized web/API security workbench.

A local, first-party toolkit for authorized HTTP/API analysis. Nothing in this
package sends a request without passing `workbench.scope.ScopeGuard`, and
nothing in it performs an access-control bypass: the design position, the
boundaries and the reasoning are in `workbench/AUTHORIZED-USE.md`.

Modules:
    scope         the authorization gate every active request passes through
    http_client   the only code that opens a socket
    history       capture, replay and comparison storage
    diff          deterministic comparison of two exchanges
    params        parameter discovery and classification
    mutate        safe request mutation
    fuzz          bounded fuzzing over mutations
    checks        observable security-property checks
    discover      scoped discovery of documents, forms and APIs
    fetch         resource acquisition and the download manifest
    extract       safe archive, PDF and document extraction
    evidence      the evidence record, redaction and hashing
    emergency     read-only incident collection and timeline
    report        report generation from evidence
    cli           the command surface
"""

__version__ = "1.0.0"
