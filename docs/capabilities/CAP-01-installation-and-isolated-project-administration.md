# CAP-01 — Installation And Isolated Project Administration

Version: 1.3
Status: ACCEPTED; direct defect-retest exception recorded; production approval not granted
Release: 0.1
Assurance: EXTENDED
Evidence state: VERIFIED — candidate `e522266`, equivalent merged tree `e348ee5`, protected run 37192774502, local-staging receipts, manual execution, and closed Softwaretest.it defects
Approval state: HUMAN ACCEPTED — product-owner acceptance recorded 2026-10-04

## Control summary

**Result:** An Administrator can bootstrap an offline installation, authenticate locally, and manage strictly isolated projects with attributable audit records.
**Evidence:** WO-CAP-01-01 through WO-CAP-01-05 are DONE. Fix candidate `e522266b8d113ddd8e6807669fb3f3abf88e3eae` was exercised in local staging as `cap01-retest-e522266-01`; merged `test` commit `e348ee5f3b6ef8f11fbcc37e417093540176c66d` has the same tree. Protected run `37192774502` passed the complete automated, package, staging/recovery, Steering, test-definition, and Softwaretest.it reporting gates. The product owner confirmed the direct retests and accepted CAP-01.
**Publication gate:** CLOSED 2026-10-01; six released definitions passed exact field-/ordered-step read-back and unchanged idempotent replay.
**Main blocker:** None for CAP-01. Softwaretest.it still displays the unused second APISTRA-TC-000006 run as `NOT_STARTED`; the platform's direct defect-retest path instead closed all three linked defects as `FIXED`, and the product owner explicitly accepted that path as authoritative for this capability.
**Next step:** Select CAP-02 for readiness review. Production approval and release promotion remain separate, ungranted gates.

## Goal and value

An Administrator can bootstrap an offline installation, authenticate locally, and manage strictly isolated projects with attributable audit records.

## Traceability

- Requirements: REQ-001, REQ-002, REQ-016, REQ-017
- Process: PRC-01
- Softwaretest.it mapping: PUBLISHED; protected run 37199065456 verified Guide 1.3.0, two RFC 8785/JCS import receipts, and complete export readback for all 160 Steering sources.
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

## Steering criterion evidence

- CAP-01-AC-01: status=PASSED; due_now=true; gate=CAP-01 acceptance; reason=The single-use bootstrap behavior passed the published manual package and protected automated matrix for the accepted candidate.
- CAP-01-AC-02: status=PASSED; due_now=true; gate=CAP-01 acceptance; reason=Revoked and expired-session behavior was corrected at e522266 and accepted after direct retest; linked defects APISTRA-D0001 and APISTRA-D0002 are CLOSED/FIXED at revision 5.
- CAP-01-AC-03: status=PASSED; due_now=true; gate=CAP-01 acceptance; reason=Own-project creation and foreign-project non-disclosure were exercised on local staging; linked defect APISTRA-D0003 is CLOSED/FIXED at revision 5.
- CAP-01-AC-04: status=PASSED; due_now=true; gate=CAP-01 acceptance; reason=Protected run 37192774502 passed the full automated and reporting gates, all linked defects are CLOSED/FIXED, and the product owner accepted the capability on 2026-10-04.

## Test and evidence contract

- BDD-AUTH-001, BDD-PROJ-001, and MT-PRC-01-001 through MT-PRC-01-006 are defined, published, and mapped to PRC-01.
- Definitions, fixtures, execution, behavioral results, reporting, defect handling, and acceptance remain separate evidence states and are reconciled in the CAP-01 acceptance record.
- The direct Softwaretest.it defect-retest path is authoritative for this acceptance: APISTRA-D0001 through APISTRA-D0003 are CLOSED/FIXED. The unused APISTRA-TC-000006 repeat remains visibly `NOT_STARTED` as a known platform-display limitation and is not relabelled as a passed run.
- Protected run `37192774502` proves the complete automated scope matrix for the unchanged merged tree.

## Workorders

- [WO-CAP-01-01](../workorders/CAP-01/WO-CAP-01-01.md)
- [WO-CAP-01-02](../workorders/CAP-01/WO-CAP-01-02.md)
- [WO-CAP-01-03](../workorders/CAP-01/WO-CAP-01-03.md)
- [WO-CAP-01-04](../workorders/CAP-01/WO-CAP-01-04.md)
- [WO-CAP-01-05](../workorders/CAP-01/WO-CAP-01-05.md)

## Staging and gate

The final workorder deployed the unchanged capability candidate to isolated local staging, executed the assigned automated and manual scope, verified recovery and Softwaretest.it state, and recorded human acceptance. Workorder DONE and capability acceptance do not grant production approval.

## Open decisions

The CAP-01 expectation, architecture, security, path, design, BDD, manual-case,
and local fixture-definition decisions are recorded in
`../planning/13-cap01-readiness-review.md`.

The authenticated Softwaretest.it publication/read-back receipt is verified
for manifest SHA-256
`b36935d8f0653d95739c259c7a41f3a1c6880ff9d67614111e7e87ce36176e5b`.
The product owner confirmed successful direct retests and CAP-01 acceptance on
2026-10-04. [The acceptance record](../testing/manual/PRC-01/acceptance-record.md)
preserves the exact candidate, protected CI run, manual run IDs, closed defects,
and the known Softwaretest.it retest-display exception. Production approval is
not inferred or granted.

