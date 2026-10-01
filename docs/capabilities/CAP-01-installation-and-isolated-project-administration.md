# CAP-01 — Installation And Isolated Project Administration

Version: 0.4-draft
Status: READY FOR SEQUENTIAL IMPLEMENTATION AFTER WO-CAP-01-04 INTEGRATION; NOT IMPLEMENTED OR ACCEPTED
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can bootstrap an offline installation, authenticate locally, and manage strictly isolated projects with attributable audit records.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Publication gate:** CLOSED 2026-10-01; six released definitions passed exact field-/ordered-step read-back and unchanged idempotent replay.
**Next step:** Integrate WO-CAP-01-04 into `test`, then move only dependency-satisfied WO-CAP-01-01 to READY and implement the remaining workorders in their declared order.

## Goal and value

An Administrator can bootstrap an offline installation, authenticate locally, and manage strictly isolated projects with attributable audit records.

## Traceability

- Requirements: REQ-001, REQ-002, REQ-016, REQ-017
- Process: PRC-01
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- single-use Administrator bootstrap
- revocable local sessions
- installation and project lifecycle
- mandatory project context
- audit and offline licence status

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-01.
- Dependencies: CAP-00
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Bootstrap is single-use and race-safe
- Project ownership is enforced server-side
- Identity remains behind a port
- Licence verification never exposes signing material

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

- ARCH rules: ARCH-001, ARCH-002, ARCH-005, ARCH-011, ARCH-012, ARCH-014
- SEC rules: SEC-001, SEC-008, SEC-014, SEC-015
- Design references: DSN-001 through DSN-004, revision 0.3, approved 2026-09-30
- Readiness review: ../planning/13-cap01-readiness-review.md
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Exactly one bootstrap Administrator can be created
2. Revoked sessions fail
3. Own-project access succeeds and foreign-project access discloses nothing
4. Critical actions are audited

## Test and evidence contract

- BDD-AUTH-001, BDD-PROJ-001, and MT-PRC-01-001 through MT-PRC-01-006 are defined locally and mapped to PRC-01.
- Definition and Softwaretest.it publication are verified; fixtures, execution, behavioral results, reporting, and acceptance remain separate evidence states.
- Deterministic fixture descriptors are implemented locally; actual staging application and verification remain capability-execution evidence.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-01-01](../workorders/CAP-01/WO-CAP-01-01.md)
- [WO-CAP-01-02](../workorders/CAP-01/WO-CAP-01-02.md)
- [WO-CAP-01-03](../workorders/CAP-01/WO-CAP-01-03.md)
- [WO-CAP-01-04](../workorders/CAP-01/WO-CAP-01-04.md)
- [WO-CAP-01-05](../workorders/CAP-01/WO-CAP-01-05.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

The CAP-01 expectation, architecture, security, path, design, BDD, manual-case,
and local fixture-definition decisions are recorded in
`../planning/13-cap01-readiness-review.md`.

The authenticated Softwaretest.it publication/read-back receipt is verified
for manifest SHA-256
`b36935d8f0653d95739c259c7a41f3a1c6880ff9d67614111e7e87ce36176e5b`.
No unresolved planning decision blocks the first dependency-satisfied
implementation workorder. Later workorders, staging execution, behavioral
evidence, capability acceptance, and production approval are not inferred.

