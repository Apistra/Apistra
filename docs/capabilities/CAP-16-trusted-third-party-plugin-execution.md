# CAP-16 — Trusted Third Party Plugin Execution

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: Later 0.x
Assurance: EXTENDED

## Control summary

**Result:** Administrators can install, inspect, execute, update, and revoke trusted third-party plugins under signed compatibility and permission contracts.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Sandbox, trust root, signing custody, permissions, and vulnerability response are blocking.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Administrators can install, inspect, execute, update, and revoke trusted third-party plugins under signed compatibility and permission contracts.

## Traceability

- Requirements: REQ-029
- Process: PRC-12
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- signature verification
- permission model
- compatibility/install
- isolated execution
- update/revocation
- SDK and compliance kit

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-12.
- Dependencies: CAP-02, CAP-03, CAP-06, CAP-15
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Unsigned packages never execute
- Permissions are least-privilege
- Plugins cannot bypass governed boundaries
- Revocation blocks new execution

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

- ARCH rules: ARCH-003, ARCH-005, ARCH-009 through ARCH-014
- SEC rules: SEC-001, SEC-002, SEC-004, SEC-006, SEC-007, SEC-011, SEC-012, SEC-015
- Design references: Plugin references pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Tampering and incompatibility are rejected
2. Undeclared access fails
3. Resources are bounded
4. Upgrade/revocation preserve history

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-12.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-16-01](../workorders/CAP-16/WO-CAP-16-01.md)
- [WO-CAP-16-02](../workorders/CAP-16/WO-CAP-16-02.md)
- [WO-CAP-16-03](../workorders/CAP-16/WO-CAP-16-03.md)
- [WO-CAP-16-04](../workorders/CAP-16/WO-CAP-16-04.md)
- [WO-CAP-16-05](../workorders/CAP-16/WO-CAP-16-05.md)
- [WO-CAP-16-06](../workorders/CAP-16/WO-CAP-16-06.md)
- [WO-CAP-16-07](../workorders/CAP-16/WO-CAP-16-07.md)
- [WO-CAP-16-08](../workorders/CAP-16/WO-CAP-16-08.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Sandbox, trust root, signing custody, permissions, and vulnerability response are blocking.

No implementing agent may resolve a blocking decision implicitly.

