# CAP-17 — Kubernetes Deployment Profile

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: Later 0.x
Assurance: EXTENDED

## Control summary

**Result:** Operators can deploy and recover the same immutable Apistra candidate on a supported Kubernetes profile without weakening the Compose baseline.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Distribution/version matrix and operator choices are blocking.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Operators can deploy and recover the same immutable Apistra candidate on a supported Kubernetes profile without weakening the Compose baseline.

## Traceability

- Requirements: REQ-030
- Process: PRC-13
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- Kubernetes packaging
- config/secrets/storage/network
- health and observability
- upgrade/rollback/restore
- hardening and conformance

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-13.
- Dependencies: Accepted 0.1 release
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Kubernetes uses the same image digests
- No cluster-specific build
- Deployment is explicit
- Compose remains supported until decided otherwise

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

- ARCH rules: ARCH-010 through ARCH-014
- SEC rules: SEC-002, SEC-004, SEC-007, SEC-011 through SEC-013, SEC-015
- Design references: Operator documentation only unless UI is separately approved
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Exact digests are verified
2. Failed rollout recovers
3. Security profile passes
4. Restore produces a coherent installation

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-13.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-17-01](../workorders/CAP-17/WO-CAP-17-01.md)
- [WO-CAP-17-02](../workorders/CAP-17/WO-CAP-17-02.md)
- [WO-CAP-17-03](../workorders/CAP-17/WO-CAP-17-03.md)
- [WO-CAP-17-04](../workorders/CAP-17/WO-CAP-17-04.md)
- [WO-CAP-17-05](../workorders/CAP-17/WO-CAP-17-05.md)
- [WO-CAP-17-06](../workorders/CAP-17/WO-CAP-17-06.md)
- [WO-CAP-17-07](../workorders/CAP-17/WO-CAP-17-07.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Distribution/version matrix and operator choices are blocking.

No implementing agent may resolve a blocking decision implicitly.

