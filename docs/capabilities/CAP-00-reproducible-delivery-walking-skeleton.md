# CAP-00 — Reproducible Delivery Walking Skeleton

Version: 0.2-draft
Status: IMPLEMENTED; acceptance gates remain
Release: 0.0
Assurance: EXTENDED

## Control summary

**Result:** A maintainer can build, verify, stage, diagnose, and recover an immutable minimal Apistra candidate without business functionality.
**Evidence:** Implementation and hosted CI evidence exist; formal acceptance is still blocked.
**Main blocker:** Branch protection, authenticated Softwaretest.it round-trip, independent review, and human acceptance remain blocking.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

A maintainer can build, verify, stage, diagnose, and recover an immutable minimal Apistra candidate without business functionality.

## Traceability

- Requirements: REQ-019, REQ-020
- Process: PRC-07
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- repository governance
- health-only web, API, and worker skeleton
- immutable packaging and SBOM
- isolated staging and recovery
- test-result reporting

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-07.
- Dependencies: None
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- No business behavior enters CAP-00
- The same immutable candidate is tested and staged
- Deployment remains human-triggered

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

- ARCH rules: ARCH-001, ARCH-010, ARCH-011, ARCH-013, ARCH-014
- SEC rules: SEC-011, SEC-012, SEC-013
- Design references: Health shell only
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. All five CI jobs pass
2. The exact candidate starts in isolated staging
3. Controlled failure recovery preserves image identity
4. External and human acceptance gates are evidenced

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-07.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-00-01](../workorders/CAP-00/WO-CAP-00-01.md)
- [WO-CAP-00-02](../workorders/CAP-00/WO-CAP-00-02.md)
- [WO-CAP-00-03](../workorders/CAP-00/WO-CAP-00-03.md)
- [WO-CAP-00-04](../workorders/CAP-00/WO-CAP-00-04.md)
- [WO-CAP-00-05](../workorders/CAP-00/WO-CAP-00-05.md)
- [WO-CAP-00-06](../workorders/CAP-00/WO-CAP-00-06.md)
- [WO-CAP-00-07](../workorders/CAP-00/WO-CAP-00-07.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Branch protection, authenticated Softwaretest.it round-trip, independent review, and human acceptance remain blocking.

No implementing agent may resolve a blocking decision implicitly.

