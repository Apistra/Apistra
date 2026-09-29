# CAP-15 — Role Based Administration And Enterprise Identity

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: Later 0.x
Assurance: EXTENDED

## Control summary

**Result:** An installation can use roles, project membership, enterprise sign-in, revocation, and separation of duties without weakening project isolation.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Provider, roles, linking, break-glass, and revocation SLA are blocking.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

An installation can use roles, project membership, enterprise sign-in, revocation, and separation of duties without weakening project isolation.

## Traceability

- Requirements: REQ-028
- Process: PRC-11
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- role/permission model
- project membership
- OIDC/SSO adapter
- account linking
- session revocation
- separation of duties

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-11.
- Dependencies: CAP-01
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Authorisation stays server-side
- External claims use an anti-corruption layer
- Revocation has a defined bound
- No role silently gains cross-project access

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

- ARCH rules: ARCH-001 through ARCH-005, ARCH-011, ARCH-012
- SEC rules: SEC-001, SEC-008, SEC-009, SEC-012, SEC-015
- Design references: IAM references pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Full role matrix passes
2. OIDC validations are enforced
3. Membership removal revokes access
4. Duty conflicts are rejected

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-11.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-15-01](../workorders/CAP-15/WO-CAP-15-01.md)
- [WO-CAP-15-02](../workorders/CAP-15/WO-CAP-15-02.md)
- [WO-CAP-15-03](../workorders/CAP-15/WO-CAP-15-03.md)
- [WO-CAP-15-04](../workorders/CAP-15/WO-CAP-15-04.md)
- [WO-CAP-15-05](../workorders/CAP-15/WO-CAP-15-05.md)
- [WO-CAP-15-06](../workorders/CAP-15/WO-CAP-15-06.md)
- [WO-CAP-15-07](../workorders/CAP-15/WO-CAP-15-07.md)
- [WO-CAP-15-08](../workorders/CAP-15/WO-CAP-15-08.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Provider, roles, linking, break-glass, and revocation SLA are blocking.

No implementing agent may resolve a blocking decision implicitly.

