# CAP-01 — Installation And Isolated Project Administration

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can bootstrap an offline installation, authenticate locally, and manage strictly isolated projects with attributable audit records.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** ADR-PENDING-004 blocks authentication implementation READY.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

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
- Design references: DSN-001 through DSN-004
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Exactly one bootstrap Administrator can be created
2. Revoked sessions fail
3. Own-project access succeeds and foreign-project access discloses nothing
4. Critical actions are audited

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-01.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
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

ADR-PENDING-004 blocks authentication implementation READY.

No implementing agent may resolve a blocking decision implicitly.

