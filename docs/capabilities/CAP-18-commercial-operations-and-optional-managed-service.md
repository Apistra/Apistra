# CAP-18 — Commercial Operations And Optional Managed Service

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: Later 0.x
Assurance: EXTENDED

## Control summary

**Result:** Operators can apply offline commercial entitlements and, if separately approved, operate a managed-service profile with explicit legal, customer, support, security, and production boundaries.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Legal terms, entitlements, signing custody, SLA, regions, subprocessors, and production controls are blocking.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Operators can apply offline commercial entitlements and, if separately approved, operate a managed-service profile with explicit legal, customer, support, security, and production boundaries.

## Traceability

- Requirements: REQ-017, REQ-031
- Process: PRC-14
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- entitlement model
- offline licence verification
- licence administration
- support bundle
- managed-service boundary
- production environment contract

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-14.
- Dependencies: CAP-01 and legal approval
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- AGPL and commercial use remain distinct
- No mandatory phone-home
- Support export is explicit and redacted
- Managed hosting needs a separate production contract

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

- ARCH rules: ARCH-003, ARCH-005, ARCH-010 through ARCH-012, ARCH-014
- SEC rules: SEC-001, SEC-002, SEC-011 through SEC-015
- Design references: Licence/support references pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Licence outcomes are deterministic
2. Signing material stays protected
3. Support bundles are secret-safe
4. Managed deployment is impossible without approval

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-14.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-18-01](../workorders/CAP-18/WO-CAP-18-01.md)
- [WO-CAP-18-02](../workorders/CAP-18/WO-CAP-18-02.md)
- [WO-CAP-18-03](../workorders/CAP-18/WO-CAP-18-03.md)
- [WO-CAP-18-04](../workorders/CAP-18/WO-CAP-18-04.md)
- [WO-CAP-18-05](../workorders/CAP-18/WO-CAP-18-05.md)
- [WO-CAP-18-06](../workorders/CAP-18/WO-CAP-18-06.md)
- [WO-CAP-18-07](../workorders/CAP-18/WO-CAP-18-07.md)
- [WO-CAP-18-08](../workorders/CAP-18/WO-CAP-18-08.md)
- [WO-CAP-18-09](../workorders/CAP-18/WO-CAP-18-09.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Legal terms, entitlements, signing custody, SLA, regions, subprocessors, and production controls are blocking.

No implementing agent may resolve a blocking decision implicitly.

