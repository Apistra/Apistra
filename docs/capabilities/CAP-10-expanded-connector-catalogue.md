# CAP-10 — Expanded Connector Catalogue

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.2
Assurance: EXTENDED

## Control summary

**Result:** Administrators can synchronise S3-compatible storage, PostgreSQL, websites, Jira, and Confluence through the same trusted connector and provenance model.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Supported API/version matrices and authorised test accounts are required per connector.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

Administrators can synchronise S3-compatible storage, PostgreSQL, websites, Jira, and Confluence through the same trusted connector and provenance model.

## Traceability

- Requirements: REQ-023
- Process: PRC-02
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- connector contract extensions
- S3 connector
- PostgreSQL connector
- website connector
- Jira connector
- Confluence connector

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-02.
- Dependencies: CAP-03 and CAP-04
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Vendor semantics remain in adapters
- New connectors cannot weaken the base contract
- Permissions and egress are explicit
- Incremental sync converges

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

- ARCH rules: ARCH-001 through ARCH-005, ARCH-009, ARCH-012, ARCH-014
- SEC rules: SEC-001, SEC-002, SEC-004, SEC-006, SEC-007, SEC-010, SEC-015
- Design references: Reuse DSN-008 and DSN-009
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Each connector passes common and target-specific suites
2. Cross-project data is denied
3. Throttling preserves cursors
4. Deletion and permission loss are safe

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-02.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-10-01](../workorders/CAP-10/WO-CAP-10-01.md)
- [WO-CAP-10-02](../workorders/CAP-10/WO-CAP-10-02.md)
- [WO-CAP-10-03](../workorders/CAP-10/WO-CAP-10-03.md)
- [WO-CAP-10-04](../workorders/CAP-10/WO-CAP-10-04.md)
- [WO-CAP-10-05](../workorders/CAP-10/WO-CAP-10-05.md)
- [WO-CAP-10-06](../workorders/CAP-10/WO-CAP-10-06.md)
- [WO-CAP-10-07](../workorders/CAP-10/WO-CAP-10-07.md)
- [WO-CAP-10-08](../workorders/CAP-10/WO-CAP-10-08.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Supported API/version matrices and authorised test accounts are required per connector.

No implementing agent may resolve a blocking decision implicitly.

