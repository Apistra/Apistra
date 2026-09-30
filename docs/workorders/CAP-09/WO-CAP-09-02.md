# WO-CAP-09-02 — Implement scheduled workflow starts

Version: 0.6-draft
Status: DRAFT
Status reason: CAP-00 and the named workorder prerequisites are not yet satisfied
Implementation state: NOT STARTED
Evidence state: NOT EXECUTED
Approval state: NOT APPROVED
Capability: [CAP-09](../../capabilities/CAP-09-scheduled-and-event-triggered-execution.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-022
- Process: PRC-09
- Capability contract: ../../capabilities/CAP-09-scheduled-and-event-triggered-execution.md
- CI test group: TST-WO-CAP-09-02
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder
- Delivery class: implementation
- Owned verification group: TST-WO-CAP-09-02
- Specification revision: 0.6-draft; earlier evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects authorization, irreversible_data, and architecture_boundary. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Implement scheduled workflow starts”; all other baseline behavior remains unchanged.

## Context and current behavior

Current evidence does not establish this 0.6 workorder result. Existing code and prior CAP-00 evidence are an observed baseline only; they do not define the expected behavior. Before READY, the readiness review must record current repository paths, public/persisted contracts, consumers, relevant configuration/identity boundaries, and any contradicting behavior.

## Target result

The capability exposes scheduled workflow starts as one integrated, versioned, project-scoped behavior through its declared application/public boundary, with safe failure and evidence for downstream work.

## Prerequisites

- Dependencies: CAP-06
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Implement only scheduled workflow starts, including its domain invariants, application use case, declared public/schema boundary, required adapter behavior, persistence/migration delta, safe errors, audit/observability, and focused documentation.
- Preserve existing capability boundaries and use only approved contracts/ADRs; no adjacent catalogue item is included.
- Add the positive, negative, boundary, compatibility, architecture, and security tests owned by this workorder.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Path authority: [Business Workorder Repository Path Contract](../../planning/12-repository-path-contract.md).

Repository observation: 2026-09-30 at commit `be7e84d`. EXISTING means the literal path was observed at that baseline; PLANNED means this workorder may create or use that exact path only after every READY prerequisite is satisfied. A path label is not implementation evidence.

Observed existing paths within the bounded change area:

- EXISTING: `docs/workorders/CAP-09/WO-CAP-09-02.md`
- EXISTING: `docs/capabilities/CAP-09-scheduled-and-event-triggered-execution.md`
- EXISTING: `CHANGELOG.md`
- EXISTING: `backend/src/apistra/modules/`
- EXISTING: `backend/src/apistra/entrypoints/api/composition.py`
- EXISTING: `backend/src/apistra/entrypoints/worker/composition.py`
- EXISTING: `apps/web/src/features/`
- EXISTING: `backend/tests/unit/`
- EXISTING: `backend/tests/component/`
- EXISTING: `backend/tests/contract/`
- EXISTING: `backend/tests/integration/`
- EXISTING: `contracts/workflow/`
- EXISTING: `contracts/openapi/`
- EXISTING: `contracts/events/`

Planned additions to the bounded change area after READY:

- PLANNED: `backend/src/apistra/modules/triggers/`
- PLANNED: `backend/src/apistra/modules/runtime/`
- PLANNED: `apps/web/src/features/triggers/`
- PLANNED: `backend/tests/unit/cap_09/`
- PLANNED: `backend/tests/component/cap_09/`
- PLANNED: `backend/tests/contract/cap_09/`
- PLANNED: `backend/tests/integration/cap_09/`
- PLANNED: `tests/bdd/features/cap_09/`
- PLANNED: `backend/src/apistra/platform/database/migrations/cap_09/`

Workorder-class boundary: Product implementation only inside the listed module, feature, contract, focused-test, optional migration, composition-root, and directly affected documentation paths.

Architecture path gate: ADR-019 top-level roots are DECIDED; planned child paths still require this workorder's expectation and architecture review before READY.

Path boundary: The EXISTING and PLANNED paths together form the upper bound after READY, not an instruction to touch every path. While this workorder is DRAFT/BLOCKED it authorises no implementation. An unlisted path, a new top-level root, a private cross-module import, or cross-module table access is a stop condition requiring observed impact, specification revision, and review.

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

- Rules: ARCH-002, ARCH-005, ARCH-006, ARCH-007, ARCH-011, ARCH-012, ARCH-013
- Applicability: the named implementation result; capability-wide rules not listed remain owned by their specific workorders or final acceptance.
- ADRs/patterns: ADR-002, ADR-003, ADR-005 through ADR-010, ADR-013, ADR-018, ADR-PENDING-003
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-005, SEC-012, SEC-015
- Applicability: the named implementation result; capability-wide rules not listed remain owned by their specific workorders or final acceptance.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. The scheduler creates one idempotent start per due occurrence using the recorded timezone and misfire policy.
2. Restart, clock shift, or duplicate scheduler delivery cannot create an unintended second occurrence.
3. All state changes are project-scoped, version/conflict checked where mutable, idempotent where redelivery is possible, and attributable through safe audit/diagnostic correlations.
4. Every public or persisted delta has a versioned contract and tested migration/compatibility behavior, or explicit evidence that no such delta exists.

## Acceptance examples and test oracles

- **Positive oracle:** The scheduler creates one idempotent start per due occurrence using the recorded timezone and misfire policy.
- **Negative oracle:** Restart, clock shift, or duplicate scheduler delivery cannot create an unintended second occurrence.
- **Boundary oracle:** Declared empty, minimum, maximum, timeout, concurrency, version, conflict, and ownership boundaries applicable to this result produce explicit documented outcomes.
- **Evidence binding:** every executed result identifies specification revision 0.6, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-022, process PRC-09, and cited architecture/security/design contracts.
- Positive expectation: The scheduler creates one idempotent start per due occurrence using the recorded timezone and misfire policy.
- Counterexample: Restart, clock shift, or duplicate scheduler delivery cannot create an unintended second occurrence.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-09-02: focused unit/component tests for the named invariants, state transitions, boundary values, and safe error taxonomy.
- Canonical BDD coverage: BDD-TRIGGER-001, BDD-TRIGGER-002, BDD-TRIGGER-003, BDD-TRIGGER-004; WO-CAP-09-05 owns the exact scenario definitions and traceability before READY.
- Contract and compatibility fixtures for each changed public/persisted schema, including unknown-version rejection.
- Architecture and security tests for the listed ARCH/SEC rules, including own-project success and foreign/anonymous/revoked denial where access exists.
- Capability regression selected by recorded change impact; WO-CAP-09-06 still owns the final complete unchanged-candidate matrix.

## BDD and manual tests

WO-CAP-09-05 must define and publish the applicable catalog-listed scenarios (BDD-TRIGGER-001, BDD-TRIGGER-002, BDD-TRIGGER-003, BDD-TRIGGER-004) before this workorder becomes READY. Manual coverage belongs to `MTP-PRC-09`; individual `MT-PRC-09-NNN` case IDs are allocated in the published package rather than invented in this implementation workorder. Execution remains with WO-CAP-09-06 unless a case is explicitly assigned here.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

This workorder produces candidate-bound evidence but does not accept the capability. WO-CAP-09-06 owns deployment of the exact complete candidate, full staging matrix, recovery, manual execution, and human acceptance.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- The four acceptance criteria and TST-WO-CAP-09-02 pass against the identified implementation snapshot
- Any assigned catalogue-listed BDD execution and workorder-owned manual/security evidence are complete
- Applicable ARCH/SEC checks, migrations, documentation, result reporting, and EXTENDED implementation review are complete
- Remaining capability-level execution stays explicitly owned by WO-CAP-09-06

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-09 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-06
- Required workorders: WO-CAP-09-01, WO-CAP-09-05
- Downstream acceptance owner: WO-CAP-09-06
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
