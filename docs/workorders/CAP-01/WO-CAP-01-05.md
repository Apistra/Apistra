# WO-CAP-01-05 — Accept CAP-01 on local staging

Version: 0.5-draft
Status: DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
Capability: [CAP-01](../../capabilities/CAP-01-installation-and-isolated-project-administration.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-001, REQ-002, REQ-016, REQ-017
- Process: PRC-01
- Capability contract: ../../capabilities/CAP-01-installation-and-isolated-project-administration.md
- CI test group: TST-WO-CAP-01-05
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder
- Delivery class: capability-acceptance
- Owned verification group: TST-WO-CAP-01-05
- Specification revision: 0.5-draft; any 0.4 evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects authorization, tenant_isolation, and secrets. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Accept CAP-01 on local staging”; all other baseline behavior remains unchanged.

## Context and current behavior

Current evidence does not establish this 0.5 workorder result. Existing code and prior CAP-00 evidence are an observed baseline only; they do not define the expected behavior. Before READY, the readiness review must record current repository paths, public/persisted contracts, consumers, relevant configuration/identity boundaries, and any contradicting behavior.

## Target result

One immutable capability candidate is fully tested, manually deployed to the named isolated staging environment, recovered, reported, independently reviewed, and presented for explicit human capability acceptance.

## Prerequisites

- Dependencies: CAP-00
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Freeze candidate identity and execute the complete capability-required CI, architecture, security, contract, BDD, migration, packaging, and recovery matrix once on that unchanged candidate.
- Manually deploy the exact digests, verify environment/fixture identity, then execute every assigned manual process/UI/security case and record step evidence, defects, and retests.
- Confirm Softwaretest.it receipts and request human capability acceptance; do not promote to production.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

No implementation path is authorised while this workorder is DRAFT/BLOCKED. Before READY, replace this paragraph through reviewed specification revision with the exact observed existing paths and any approved new path from ADR-019. The allowed set must be limited to the owning module/public contract, necessary entrypoint or UI adapter, language-neutral schema, focused tests/fixtures, migration if required, and directly affected documentation. Private cross-module imports and cross-module table access remain forbidden.

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

- Rules: ARCH-001, ARCH-002, ARCH-005, ARCH-011, ARCH-012, ARCH-014
- ADRs/patterns: ADR-001 through ADR-005, ADR-010, ADR-013, ADR-017, ADR-018, ADR-PENDING-004
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-008, SEC-014, SEC-015
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. Every prerequisite workorder is DONE and no blocking or expired exception remains.
2. The complete required matrix passes on one unchanged commit/candidate with current suite and input fingerprints.
3. The same digests are staged manually; migration, health, smoke, observability, controlled failure, recovery, and all assigned manual cases pass with confirmed reporting.
4. An authorised human accepts the exact capability/candidate/environment evidence package; no production approval is inferred.

## Acceptance examples and test oracles

- **Positive oracle:** The full required matrix and manual package pass on the exact candidate digests deployed to the named staging environment, followed by explicit human acceptance.
- **Negative oracle:** A changed digest, missing/stale/skipped mandatory result, failed recovery, absent receipt, or missing human decision blocks capability acceptance.
- **Boundary oracle:** Acceptance covers the declared minimum and maximum supported configuration plus timeout, retry, concurrency, recovery, and compatibility edges applicable to the capability.
- **Evidence binding:** every executed result identifies specification revision 0.5, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-001, REQ-002, REQ-016, REQ-017, process PRC-01, and cited architecture/security/design contracts.
- Positive expectation: The full required matrix and manual package pass on the exact candidate digests deployed to the named staging environment, followed by explicit human acceptance.
- Counterexample: A changed digest, missing/stale/skipped mandatory result, failed recovery, absent receipt, or missing human decision blocks capability acceptance.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-01-05: gate completeness, candidate/digest equality, evidence freshness, and receipt validation.
- Full capability CI and BDD matrix on the unchanged candidate; no selective reuse substitutes for this final run.
- Every published `MT-*` case for PRC-01 executed on staging with atomic step results.
- Recovery and rollback/roll-forward drill appropriate to the capability's state and external effects.

## BDD and manual tests

Execute the complete published capability BDD catalogue and `MTP-PRC-01` manual package. Missing, stale, skipped without approved disposition, or unreported mandatory cases block this workorder.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

This workorder owns the capability staging gate. Candidate manifest, image digests, configuration, fixture version, deployment marker, health/smoke, diagnostics, recovery, Softwaretest.it receipts, and human decision must identify the same attempt.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- All prerequisite workorders are DONE with current evidence
- Full matrix and required manual cases pass on the exact staged candidate
- Reporting receipts, recovery evidence, and independent implementation review are complete
- Authorised human capability acceptance is recorded; production remains separately unapproved

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-01 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-00
- Required workorders: WO-CAP-01-01, WO-CAP-01-02, WO-CAP-01-03, WO-CAP-01-04
- Downstream acceptance owner: none; this is the capability acceptance workorder
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
