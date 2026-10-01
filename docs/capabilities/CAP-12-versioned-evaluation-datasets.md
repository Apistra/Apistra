# CAP-12 — Versioned Evaluation Datasets

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.3
Assurance: EXTENDED

## Control summary

**Result:** AI engineers can define immutable evaluation dataset versions with traceable inputs, expected properties, provenance, and deterministic selection.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Retention and sensitive-fixture classification require approval.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

AI engineers can define immutable evaluation dataset versions with traceable inputs, expected properties, provenance, and deterministic selection.

## Traceability

- Requirements: REQ-025
- Process: PRC-06
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- dataset schema
- case lifecycle
- fixture import
- deterministic runner
- result/evidence model

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-06.
- Dependencies: CAP-05 and CAP-06
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Published datasets are immutable
- Sensitive values use references or synthetic data
- Results identify dataset, case, candidate, and attempt
- Deterministic and subjective expectations are distinct

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

- ARCH rules: ARCH-001, ARCH-002, ARCH-005 through ARCH-007, ARCH-012
- SEC rules: SEC-001, SEC-002, SEC-005, SEC-007, SEC-012, SEC-015
- Design references: Dataset catalogue/editor/version references pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Case selection is stable
2. Invalid or secret-bearing imports fail safely
3. Results retain fingerprints
4. Updates create new versions

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-06.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-12-01](../workorders/CAP-12/WO-CAP-12-01.md)
- [WO-CAP-12-02](../workorders/CAP-12/WO-CAP-12-02.md)
- [WO-CAP-12-03](../workorders/CAP-12/WO-CAP-12-03.md)
- [WO-CAP-12-04](../workorders/CAP-12/WO-CAP-12-04.md)
- [WO-CAP-12-05](../workorders/CAP-12/WO-CAP-12-05.md)
- [WO-CAP-12-06](../workorders/CAP-12/WO-CAP-12-06.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Retention and sensitive-fixture classification require approval.

No implementing agent may resolve a blocking decision implicitly.

