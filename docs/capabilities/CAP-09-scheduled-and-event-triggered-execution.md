# CAP-09 — Scheduled And Event Triggered Execution

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.2
Assurance: EXTENDED

## Control summary

**Result:** Administrators can trigger published workflows from schedules or authenticated events with replay protection and bounded catch-up behavior.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Scheduler/event-transport ADR and catch-up defaults are blocking.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Administrators can trigger published workflows from schedules or authenticated events with replay protection and bounded catch-up behavior.

## Traceability

- Requirements: REQ-022
- Process: PRC-09
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- trigger model
- scheduler
- event ingress
- replay protection
- missed-event and catch-up policy

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-09.
- Dependencies: CAP-06
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Triggers target immutable workflow versions
- Replay keys are project-scoped
- Catch-up is explicit and bounded
- Disablement prevents new starts

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

- ARCH rules: ARCH-002, ARCH-003, ARCH-008, ARCH-009, ARCH-012, ARCH-014
- SEC rules: SEC-001, SEC-004, SEC-006, SEC-007, SEC-015
- Design references: Trigger catalogue, editor, and history references pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Duplicate events create one run
2. Timezone handling is deterministic
3. Missed events follow policy
4. Paused/disabled state is audited

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-09.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-09-01](../workorders/CAP-09/WO-CAP-09-01.md)
- [WO-CAP-09-02](../workorders/CAP-09/WO-CAP-09-02.md)
- [WO-CAP-09-03](../workorders/CAP-09/WO-CAP-09-03.md)
- [WO-CAP-09-04](../workorders/CAP-09/WO-CAP-09-04.md)
- [WO-CAP-09-05](../workorders/CAP-09/WO-CAP-09-05.md)
- [WO-CAP-09-06](../workorders/CAP-09/WO-CAP-09-06.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Scheduler/event-transport ADR and catch-up defaults are blocking.

No implementing agent may resolve a blocking decision implicitly.

