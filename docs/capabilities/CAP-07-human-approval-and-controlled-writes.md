# CAP-07 — Human Approval And Controlled Writes

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** A governed write pauses durably, can be approved or rejected through UI or API, and resumes or terminates exactly once with complete auditability.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Expiry and exception-policy granularity require confirmation.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

A governed write pauses durably, can be approved or rejected through UI or API, and resumes or terminates exactly once with complete auditability.

## Traceability

- Requirements: REQ-012, REQ-016
- Process: PRC-05
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- write policy
- durable human tasks
- approval inbox and detail
- decision API
- rejection and timeout paths

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-05.
- Dependencies: CAP-02, CAP-05, CAP-06
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Writes require approval by default
- Only authorised Administrators decide in 0.1
- Rejection requires a reason
- Timeout never approves

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

- ARCH rules: ARCH-001, ARCH-002, ARCH-005, ARCH-008, ARCH-009, ARCH-011, ARCH-015
- SEC rules: SEC-001, SEC-002, SEC-003, SEC-006, SEC-007, SEC-015
- Design references: DSN-017 and DSN-018
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Task detail is complete and secret-safe
2. Approval resumes once
3. Rejection and timeout do not execute
4. All decisions are audited

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-05.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-07-01](../workorders/CAP-07/WO-CAP-07-01.md)
- [WO-CAP-07-02](../workorders/CAP-07/WO-CAP-07-02.md)
- [WO-CAP-07-03](../workorders/CAP-07/WO-CAP-07-03.md)
- [WO-CAP-07-04](../workorders/CAP-07/WO-CAP-07-04.md)
- [WO-CAP-07-05](../workorders/CAP-07/WO-CAP-07-05.md)
- [WO-CAP-07-06](../workorders/CAP-07/WO-CAP-07-06.md)
- [WO-CAP-07-07](../workorders/CAP-07/WO-CAP-07-07.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Expiry and exception-policy granularity require confirmation.

No implementing agent may resolve a blocking decision implicitly.

