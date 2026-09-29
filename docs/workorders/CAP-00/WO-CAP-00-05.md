# WO-CAP-00-05 — Establish Softwaretest.it publishing readiness

Version: 0.5-draft
Status: PARTIALLY IMPLEMENTED; authenticated round-trip is blocked
Capability: [CAP-00](../../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-019, REQ-020
- Process: PRC-07
- Capability contract: ../../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md
- CI test group: TST-WO-CAP-00-05
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder
- Delivery class: test-definition-and-publication
- Owned verification group: TST-WO-CAP-00-05
- Specification revision: 0.5-draft; any 0.4 evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects delivery_control and architecture_boundary. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Establish Softwaretest.it publishing readiness”; all other baseline behavior remains unchanged.

## Context and current behavior

CAP-00 implementation and hosted evidence exist against the 0.4 workorder revision. This 0.5 revision strengthens the execution and evidence contract without claiming a new implementation result. A documented change-impact review must identify which prior evidence remains valid and which checks or approvals must be repeated.

## Target result

The complete PRC-07 capability test package is versioned locally, idempotently published to Softwaretest.it, and verified by field- and step-level read-back before behavioral implementation becomes READY.

## Prerequisites

- Dependencies: None
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Derive automated BDD scenarios, independent manual process/UI/security cases, atomic steps, fixtures, roles, data, requirement/risk links, and CI-stage mappings from the approved capability contracts.
- Publish or update definitions idempotently through the verified API and read back identifiers, fields, ordering, and links.
- Preserve a lossless local manifest/outbox when authorised publication is unavailable; do not execute the tests in this workorder.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Observed path scope for this completed bootstrap slice: engineering/softwaretest/, result-bundle contracts, and CI reporting configuration. Any change outside these paths requires an explicit scope/impact update before work continues.

## Stop conditions

- CAP-00 or another prerequisite is not accepted
- A required ADR, schema, identity, project boundary, design state, authorised test target, or Softwaretest.it resource is missing
- The observed repository contradicts this workorder
- Acceptance would require an unlisted external mutation, destructive test, or production deployment
- A blocking architecture/security finding or ambiguous expected behavior appears

## Technical guardrails

- Application Service/use-case entrypoints coordinate behavior; domain code remains framework-independent.
- Ports and Adapters apply only at volatile or security-relevant boundaries.
- Persisted lifecycles use explicit state machines; external redelivery uses outbox/inbox/idempotency where applicable.
- Schema-first boundary mappers prevent vendor or transport models from entering domain code.
- Mutable administration uses optimistic concurrency; no global CQRS or Event Sourcing is introduced.

No new UI is authorised unless the capability design contract explicitly assigns one.

## ARCH rules and pattern limits

- Rules: ARCH-001, ARCH-010, ARCH-011, ARCH-013, ARCH-014
- ADRs/patterns: ADR-017 and ADR-019
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-011, SEC-012, SEC-013
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. Every externally observable capability acceptance criterion has a stable BDD ID or an explicit not-applicable rationale.
2. Every business process has a complete manual package starting at logged-out sign-in, with atomic role-prefixed action/observation steps, concrete synthetic data, and one matching expected result per step.
3. Publication is idempotent and field-/order-level read-back matches the local version and checksums.
4. Definition, publication, fixture readiness, execution, result reporting, and capability acceptance remain distinct statuses.

## Acceptance examples and test oracles

- **Positive oracle:** The complete PRC-07 package publishes idempotently and read-back preserves every ID, field, traceability link, and manual-step order.
- **Negative oracle:** A missing case, flattened/reordered step, changed field, duplicate object, or absent authorised receipt leaves publication unverified and blocks dependent READY.
- **Boundary oracle:** Empty, single-case, maximum supported, repeated, and partially rejected publication requests retain deterministic IDs and atomic outcomes.
- **Evidence binding:** every executed result identifies specification revision 0.5, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-019, REQ-020, process PRC-07, and cited architecture/security/design contracts.
- Positive expectation: The complete PRC-07 package publishes idempotently and read-back preserves every ID, field, traceability link, and manual-step order.
- Counterexample: A missing case, flattened/reordered step, changed field, duplicate object, or absent authorised receipt leaves publication unverified and blocks dependent READY.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-00-05: definition schema, ID uniqueness, traceability, atomic-step structure, and local manifest validation in CI-TS-01/CI-TS-06.
- Softwaretest.it adapter contract and idempotency tests in CI-TS-06 and CI-TS-16.
- Authorised live round-trip proving project/plan/case fields and manual-step order.
- No behavioral test result is created by publishing a definition.

## BDD and manual tests

This workorder owns definition/publication of all planned `BDD-CAP-*`, `BDD-WO-*`, `MTP-PRC-07`, and `MT-*` IDs for the capability. Execution remains with the owning implementation workorder or WO-CAP-00-07 as explicitly assigned in each definition.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

No product candidate is accepted. Only the engineering test-management target is changed, using minimum authorised project-scoped credentials and a lossless local outbox on failure.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- Complete local test package and traceability manifest pass structural review
- Authorised Softwaretest.it publication and field-/step-level read-back are confirmed, or the workorder remains BLOCKED
- Consumer workorders reference stable IDs and execution ownership
- No unexecuted definition is reported as a passed test

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-00 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: None
- Required workorders: WO-CAP-00-01, WO-CAP-00-02, WO-CAP-00-03, WO-CAP-00-04
- Downstream acceptance owner: WO-CAP-00-07
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
