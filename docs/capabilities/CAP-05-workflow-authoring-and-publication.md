# CAP-05 — Workflow Authoring And Publication

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can author one canonical workflow visually or as YAML/JSON, validate and test it, and publish an immutable version.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Product-owner design approval and detailed interaction-state references block UI READY.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

An Administrator can author one canonical workflow visually or as YAML/JSON, validate and test it, and publish an immutable version.

## Traceability

- Requirements: REQ-008, REQ-009, REQ-018
- Process: PRC-03
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- canonical workflow schema
- graph and node validation
- visual editor
- YAML/JSON round-trip
- draft conflicts
- immutable publication

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-03.
- Dependencies: CAP-01 through CAP-04
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Visual and text views project one canonical model
- Drafts are mutable and published versions immutable
- Publication captures all non-secret version references
- Old versions remain callable until disabled

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

- ARCH rules: ARCH-001, ARCH-002, ARCH-005 through ARCH-007, ARCH-011 through ARCH-013
- SEC rules: SEC-001, SEC-002, SEC-005, SEC-007, SEC-015
- Design references: DSN-009 through DSN-014
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Round-trip preserves semantics
2. Validation identifies exact graph locations
3. Concurrent edits create explicit conflicts
4. Published snapshots reject mutation

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-03.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-05-01](../workorders/CAP-05/WO-CAP-05-01.md)
- [WO-CAP-05-02](../workorders/CAP-05/WO-CAP-05-02.md)
- [WO-CAP-05-03](../workorders/CAP-05/WO-CAP-05-03.md)
- [WO-CAP-05-04](../workorders/CAP-05/WO-CAP-05-04.md)
- [WO-CAP-05-05](../workorders/CAP-05/WO-CAP-05-05.md)
- [WO-CAP-05-06](../workorders/CAP-05/WO-CAP-05-06.md)
- [WO-CAP-05-07](../workorders/CAP-05/WO-CAP-05-07.md)
- [WO-CAP-05-08](../workorders/CAP-05/WO-CAP-05-08.md)
- [WO-CAP-05-09](../workorders/CAP-05/WO-CAP-05-09.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Product-owner design approval and detailed interaction-state references block UI READY.

No implementing agent may resolve a blocking decision implicitly.

