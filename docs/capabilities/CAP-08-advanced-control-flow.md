# CAP-08 — Advanced Control Flow

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.2
Assurance: EXTENDED

## Control summary

**Result:** Workflow authors can use durable parallelism, merging, bounded iteration, subflows, fallback, human input, and human editing without weakening recovery or versioning.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Merge, compensation, loop-bound, and subflow-version semantics require review.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Workflow authors can use durable parallelism, merging, bounded iteration, subflows, fallback, human input, and human editing without weakening recovery or versioning.

## Traceability

- Requirements: REQ-021
- Process: PRC-08
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- advanced-node schemas
- parallel and merge
- loops and for-each
- subflows
- fallback
- human input and edit

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-08.
- Dependencies: CAP-05 through CAP-07
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Fan-out and iteration are bounded
- Merge semantics are explicit
- Subflow versions are snapshotted
- Human edits preserve history

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

- ARCH rules: ARCH-002, ARCH-006 through ARCH-009, ARCH-012
- SEC rules: SEC-001, SEC-003, SEC-006, SEC-007, SEC-015
- Design references: Extensions of DSN-010 and DSN-018
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Every construct resumes safely
2. Bounds violations are stable results
3. Subflow/fallback paths are traceable
4. Human edits are authorised and audited

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-08.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-08-01](../workorders/CAP-08/WO-CAP-08-01.md)
- [WO-CAP-08-02](../workorders/CAP-08/WO-CAP-08-02.md)
- [WO-CAP-08-03](../workorders/CAP-08/WO-CAP-08-03.md)
- [WO-CAP-08-04](../workorders/CAP-08/WO-CAP-08-04.md)
- [WO-CAP-08-05](../workorders/CAP-08/WO-CAP-08-05.md)
- [WO-CAP-08-06](../workorders/CAP-08/WO-CAP-08-06.md)
- [WO-CAP-08-07](../workorders/CAP-08/WO-CAP-08-07.md)
- [WO-CAP-08-08](../workorders/CAP-08/WO-CAP-08-08.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Merge, compensation, loop-bound, and subflow-version semantics require review.

No implementing agent may resolve a blocking decision implicitly.

