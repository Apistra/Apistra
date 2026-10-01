# CAP-03 — Connector Foundation And Trusted Sources

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can configure and synchronise file/directory, REST, and Git sources through a stable connector contract with bounded egress and safe retries.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Scheduled synchronisation depends on the local scheduler/transport decision.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

An Administrator can configure and synchronise file/directory, REST, and Git sources through a stable connector contract with bounded egress and safe retries.

## Traceability

- Requirements: REQ-006, REQ-014
- Process: PRC-02
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- connector SDK and compliance kit
- file/directory connector
- REST connector
- Git connector
- full and incremental synchronisation

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-02.
- Dependencies: CAP-01 and CAP-02
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Connectors emit canonical documents with provenance
- Egress is allowlisted
- Retries cannot duplicate active records
- Credentials remain references

## Main flow

1. The authorised actor selects the project and versioned inputs.
2. Apistra validates identity, ownership, policy, schema, limits, and references.
3. The application use case performs the bounded operation through declared ports.
4. State, evidence, diagnostics, and audit data are committed with correlation identifiers.
5. A stable result or safe actionable error is returned.

## Alternative and failure flows

- Invalid, incompatible, unauthorised, or foreign-project input is rejected without data disclosure.
- Retriable failure preserves committed state and cannot duplicate completed effects.
- Policy, limit, approval, and security denials are first-class audited outcomes.

## Data, interfaces, and states

- Mutable administration uses explicit version/conflict handling; published versions are immutable.
- Public contracts are schema-first and versioned; vendor semantics remain in adapters.
- Cross-module access uses public contracts only; secrets remain protected references.
- External effects require idempotency, bounded retry, and stable error translation.

## Architecture, security, and design

- ARCH rules: ARCH-001, ARCH-002, ARCH-003, ARCH-005, ARCH-009, ARCH-012, ARCH-014
- SEC rules: SEC-001, SEC-002, SEC-004, SEC-006, SEC-007, SEC-015
- Design references: DSN-007 and DSN-008
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Each built-in connector passes the compliance suite
2. SSRF targets and unsafe redirects are blocked
3. Repeated sync converges
4. Errors are correlated and redacted

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-02.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-03-01](../workorders/CAP-03/WO-CAP-03-01.md)
- [WO-CAP-03-02](../workorders/CAP-03/WO-CAP-03-02.md)
- [WO-CAP-03-03](../workorders/CAP-03/WO-CAP-03-03.md)
- [WO-CAP-03-04](../workorders/CAP-03/WO-CAP-03-04.md)
- [WO-CAP-03-05](../workorders/CAP-03/WO-CAP-03-05.md)
- [WO-CAP-03-06](../workorders/CAP-03/WO-CAP-03-06.md)
- [WO-CAP-03-07](../workorders/CAP-03/WO-CAP-03-07.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Scheduled synchronisation depends on the local scheduler/transport decision.

No implementing agent may resolve a blocking decision implicitly.

