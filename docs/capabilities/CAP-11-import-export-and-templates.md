# CAP-11 — Import Export And Templates

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.2
Assurance: EXTENDED

## Control summary

**Result:** Administrators can inspect, export, import, and reuse reviewed project assets across compatible installations without exporting secrets or violating ownership.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Template trust/signing and compatibility-window policies require approval.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Administrators can inspect, export, import, and reuse reviewed project assets across compatible installations without exporting secrets or violating ownership.

## Traceability

- Requirements: REQ-024
- Process: PRC-10
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- export manifest
- secret-free package
- import preview
- compatibility and conflicts
- ownership enforcement
- templates

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-10.
- Dependencies: CAP-01 through CAP-07
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Secrets are never exported
- Import is previewed before mutation
- Destination ownership is enforced
- Unknown versions fail without partial mutation

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

- ARCH rules: ARCH-003 through ARCH-007, ARCH-009, ARCH-012
- SEC rules: SEC-001, SEC-002, SEC-005, SEC-012, SEC-015
- Design references: Import/export/template references pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Checksummed exports contain no secret values
2. Preview lists all changes/conflicts
3. Foreign references are denied
4. Interrupted import is retry-safe

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-10.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-11-01](../workorders/CAP-11/WO-CAP-11-01.md)
- [WO-CAP-11-02](../workorders/CAP-11/WO-CAP-11-02.md)
- [WO-CAP-11-03](../workorders/CAP-11/WO-CAP-11-03.md)
- [WO-CAP-11-04](../workorders/CAP-11/WO-CAP-11-04.md)
- [WO-CAP-11-05](../workorders/CAP-11/WO-CAP-11-05.md)
- [WO-CAP-11-06](../workorders/CAP-11/WO-CAP-11-06.md)
- [WO-CAP-11-07](../workorders/CAP-11/WO-CAP-11-07.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Template trust/signing and compatibility-window policies require approval.

No implementing agent may resolve a blocking decision implicitly.

