# CAP-04 — Knowledge And Cited Retrieval

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can create versioned knowledge indexes, retrieve cited content, and prove that stale or deleted source material is ineligible for retrieval.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Retention defaults and deletion mode require product/security confirmation.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

An Administrator can create versioned knowledge indexes, retrieve cited content, and prove that stale or deleted source material is ineligible for retrieval.

## Traceability

- Requirements: REQ-007
- Process: PRC-02
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- document/provenance model
- extraction and chunking
- versioned embeddings
- Qdrant adapter
- cited retrieval
- deletion and reconciliation

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-02.
- Dependencies: CAP-02 and CAP-03
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Every chunk maps to source, version, and location
- Embedding and chunking configuration is versioned
- Deletion removes retrieval eligibility
- Citation policy is explicit

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
- SEC rules: SEC-001, SEC-002, SEC-006, SEC-007, SEC-010, SEC-015
- Design references: DSN-008 and retrieval inspection states
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Retrieval returns complete provenance
2. Re-indexing is idempotent
3. Deleted sources leave no eligible stale vectors
4. Reconciliation detects orphans

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-02.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-04-01](../workorders/CAP-04/WO-CAP-04-01.md)
- [WO-CAP-04-02](../workorders/CAP-04/WO-CAP-04-02.md)
- [WO-CAP-04-03](../workorders/CAP-04/WO-CAP-04-03.md)
- [WO-CAP-04-04](../workorders/CAP-04/WO-CAP-04-04.md)
- [WO-CAP-04-05](../workorders/CAP-04/WO-CAP-04-05.md)
- [WO-CAP-04-06](../workorders/CAP-04/WO-CAP-04-06.md)
- [WO-CAP-04-07](../workorders/CAP-04/WO-CAP-04-07.md)
- [WO-CAP-04-08](../workorders/CAP-04/WO-CAP-04-08.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Retention defaults and deletion mode require product/security confirmation.

No implementing agent may resolve a blocking decision implicitly.

