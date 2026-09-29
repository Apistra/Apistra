# CAP-06 — Durable Process Api

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An API client can start, observe, cancel, and obtain schema-valid results from a durable, idempotent workflow run.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** ADR-PENDING-001 and callback-signing decisions block affected workorders.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

An API client can start, observe, cancel, and obtain schema-valid results from a durable, idempotent workflow run.

## Traceability

- Requirements: REQ-010, REQ-011, REQ-013, REQ-015, REQ-016
- Process: PRC-04
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- durable engine
- run and attempt states
- Process API
- API keys and start idempotency
- checkpoints and cancellation
- callbacks and run trace

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-04.
- Dependencies: CAP-01, CAP-02, CAP-04, CAP-05
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Start returns 202 and a run ID
- Equivalent idempotency replay returns the same run
- Effects are idempotent or compensated
- Recovery resumes from committed checkpoints

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

- ARCH rules: ARCH-001 through ARCH-005, ARCH-008 through ARCH-014
- SEC rules: SEC-001, SEC-002, SEC-004, SEC-006, SEC-007, SEC-009, SEC-013, SEC-015, SEC-016
- Design references: DSN-014 through DSN-016
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Worker restart resumes safely
2. Conflicting idempotency reuse fails
3. Cancellation reaches a defined state
4. Output validates and callbacks are protected

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-04.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-06-01](../workorders/CAP-06/WO-CAP-06-01.md)
- [WO-CAP-06-02](../workorders/CAP-06/WO-CAP-06-02.md)
- [WO-CAP-06-03](../workorders/CAP-06/WO-CAP-06-03.md)
- [WO-CAP-06-04](../workorders/CAP-06/WO-CAP-06-04.md)
- [WO-CAP-06-05](../workorders/CAP-06/WO-CAP-06-05.md)
- [WO-CAP-06-06](../workorders/CAP-06/WO-CAP-06-06.md)
- [WO-CAP-06-07](../workorders/CAP-06/WO-CAP-06-07.md)
- [WO-CAP-06-08](../workorders/CAP-06/WO-CAP-06-08.md)
- [WO-CAP-06-09](../workorders/CAP-06/WO-CAP-06-09.md)
- [WO-CAP-06-10](../workorders/CAP-06/WO-CAP-06-10.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

ADR-PENDING-001 and callback-signing decisions block affected workorders.

No implementing agent may resolve a blocking decision implicitly.

