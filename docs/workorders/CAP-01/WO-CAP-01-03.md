# WO-CAP-01-03 — Implement project-context enforcement and audit

Version: 0.9-done
Status: DONE
Status reason: owned implementation, conformance review, local immutable staging/recovery, and hosted CI matrix complete; capability acceptance remains with WO-CAP-01-05
Implementation state: COMPLETE AT `0e4b8674f39102860416ee4614c64a1aa19647dd`
Evidence state: LOCAL AND HOSTED OWNED MATRIX VERIFIED
Approval state: CAP-01 PLANNING APPROVED; WO-CAP-01-03 IMPLEMENTATION CONFORMANCE APPROVED
Capability: [CAP-01](../../capabilities/CAP-01-installation-and-isolated-project-administration.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-001, REQ-002, REQ-016, REQ-017
- Process: PRC-01
- Capability contract: ../../capabilities/CAP-01-installation-and-isolated-project-administration.md
- CI test group: TST-WO-CAP-01-03
- Softwaretest.it mapping: PUBLISHED AND VERIFIED by WO-CAP-01-04; APISTRA-TC-000002 through APISTRA-TC-000007
- Delivery class: implementation
- Owned verification group: TST-WO-CAP-01-03
- Specification revision: 0.9-done earlier evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects authorization, tenant_isolation, and secrets. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Implement project-context enforcement and audit”; all other baseline behavior remains unchanged.

## Context and current behavior

Project-context enforcement and attributable audit are implemented at `0e4b8674f39102860416ee4614c64a1aa19647dd`. Owner-scoped application/adapter reads, an authenticated aggregate audit API, safe project-route behavior, the approved audit labels, and immutable staging/recovery are locally verified. Hosted run `36900029244` passed the complete feature-branch matrix at `478146c`; final capability acceptance remains separate in WO-CAP-01-05.

## Target result

The capability exposes project-context enforcement and audit as one integrated, versioned, project-scoped behavior through its declared application/public boundary, with safe failure and evidence for downstream work.

## Prerequisites

- Dependencies: CAP-00
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Implement only project-context enforcement and audit, including its domain invariants, application use case, declared public/schema boundary, required adapter behavior, persistence/migration delta, safe errors, audit/observability, and focused documentation.
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

- EXISTING: `docs/workorders/CAP-01/WO-CAP-01-03.md`
- EXISTING: `docs/capabilities/CAP-01-installation-and-isolated-project-administration.md`
- EXISTING: `CHANGELOG.md`
- EXISTING: `backend/src/apistra/modules/`
- EXISTING: `backend/src/apistra/entrypoints/api/composition.py`
- EXISTING: `backend/src/apistra/entrypoints/worker/composition.py`
- EXISTING: `apps/web/src/features/`
- EXISTING: `backend/tests/unit/`
- EXISTING: `backend/tests/component/`
- EXISTING: `backend/tests/contract/`
- EXISTING: `backend/tests/integration/`
- EXISTING: `backend/src/apistra/modules/projects/`
- EXISTING: `contracts/openapi/`
- EXISTING: `contracts/events/`
- EXISTING: `apps/web/src/app/`
- EXISTING: `contracts/openapi/cap01-administration.openapi.json`
- EXISTING: `tools/staging/verify_candidate.py`

Planned additions to the bounded change area after READY:

- PLANNED: `backend/src/apistra/modules/identity/`
- PLANNED: `apps/web/src/features/administration/`
- PLANNED: `backend/tests/unit/cap_01/`
- PLANNED: `backend/tests/component/cap_01/`
- PLANNED: `backend/tests/contract/cap_01/`
- PLANNED: `backend/tests/integration/cap_01/`
- PLANNED: `tests/bdd/features/cap_01/`
- PLANNED: `backend/src/apistra/platform/database/migrations/cap_01/`

Workorder-class boundary: Product implementation only inside the listed module, feature, contract, focused-test, optional migration, composition-root, and directly affected documentation paths.

Architecture path gate: DECIDED for CAP-01 by ADR-019 and the approved CAP-01 mapping; an unlisted path or new root remains blocking.

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

- Rules: ARCH-001, ARCH-002, ARCH-003, ARCH-005, ARCH-011, ARCH-012
- Applicability: the named implementation result; capability-wide rules not listed remain owned by their specific workorders or final acceptance.
- ADRs/patterns: ADR-001, ADR-002, ADR-003, ADR-004, ADR-013, ADR-017, ADR-018, ADR-019, ADR-021
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-002, SEC-007, SEC-012, SEC-015
- Applicability: the named implementation result; capability-wide rules not listed remain owned by their specific workorders or final acceptance.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. Every project-owned use case receives and audits the authenticated project context before repository or adapter access.
2. A missing or mismatched project context fails before data access and cannot be bypassed through a direct API call.
3. All state changes are project-scoped, version/conflict checked where mutable, idempotent where redelivery is possible, and attributable through safe audit/diagnostic correlations.
4. Every public or persisted delta has a versioned contract and tested migration/compatibility behavior, or explicit evidence that no such delta exists.

## Steering criterion evidence

- WO-CAP-01-03-AC-01: status=PASSED; due_now=true; gate=WO-CAP-01-03 completion; reason=The project-context component and integration tests verified authenticated project context before project-owned use cases reach repositories or adapters.
- WO-CAP-01-03-AC-02: status=PASSED; due_now=true; gate=WO-CAP-01-03 completion; reason=Missing, mismatched, anonymous, and foreign-project context tests reject direct API requests before protected data access.
- WO-CAP-01-03-AC-03: status=PASSED; due_now=true; gate=WO-CAP-01-03 completion; reason=Project-bound application and adapter paths passed the owned local and hosted architecture, authorization, and audit checks.
- WO-CAP-01-03-AC-04: status=PASSED; due_now=true; gate=WO-CAP-01-03 completion; reason=The project-context boundary is covered by versioned API/consumer contracts and the applicable compatibility matrix; this workorder added no independent persisted schema.

## Acceptance examples and test oracles

- **Positive oracle:** Every project-owned use case receives and audits the authenticated project context before repository or adapter access.
- **Negative oracle:** A missing or mismatched project context fails before data access and cannot be bypassed through a direct API call.
- **Boundary oracle:** Declared empty, minimum, maximum, timeout, concurrency, version, conflict, and ownership boundaries applicable to this result produce explicit documented outcomes.
- **Evidence binding:** every executed result identifies specification revision 0.7, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-001, REQ-002, REQ-016, REQ-017, process PRC-01, and cited architecture/security/design contracts.
- Positive expectation: Every project-owned use case receives and audits the authenticated project context before repository or adapter access.
- Counterexample: A missing or mismatched project context fails before data access and cannot be bypassed through a direct API call.
- The independent derivation, comparison, discrepancy resolution, and human confirmation are recorded in ../../planning/13-cap01-readiness-review.md; a material source change invalidates that review.

## Required tests

- TST-WO-CAP-01-03: focused unit/component tests for the named invariants, state transitions, boundary values, and safe error taxonomy.
- Canonical BDD coverage: BDD-AUTH-001, BDD-PROJ-001; WO-CAP-01-04 owns the exact scenario definitions and traceability before READY.
- Contract and compatibility fixtures for each changed public/persisted schema, including unknown-version rejection.
- Architecture and security tests for the listed ARCH/SEC rules, including own-project success and foreign/anonymous/revoked denial where access exists.
- Capability regression selected by recorded change impact; WO-CAP-01-05 still owns the final complete unchanged-candidate matrix.

## BDD and manual tests

WO-CAP-01-04 must define and publish the applicable catalog-listed scenarios (BDD-AUTH-001, BDD-PROJ-001) before this workorder becomes READY. Manual coverage belongs to `MTP-PRC-01`; individual `MT-PRC-01-NNN` case IDs are allocated in the published package rather than invented in this implementation workorder. Execution remains with WO-CAP-01-05 unless a case is explicitly assigned here.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

This workorder produces candidate-bound evidence but does not accept the capability. WO-CAP-01-05 owns deployment of the exact complete candidate, full staging matrix, recovery, manual execution, and human acceptance.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

Observed local evidence for implementation snapshot `0e4b8674f39102860416ee4614c64a1aa19647dd`:

- The exact CI-style backend matrix passed 76 tests against PostgreSQL 17.6 with 91.38% aggregate coverage.
- Eleven web tests passed with 100% imported line/function coverage; TypeScript typecheck, production build, and TypeScript architecture rules passed.
- Python architecture fixtures, eight Import Linter contracts, repository contracts and negative fixtures, Ruff format/static checks, and the secret-scan negative fixture passed.
- Twenty-seven Softwaretest.it adapter/definition contract tests, the local definition manifest, and the public integration-guide preflight passed without an external mutation.
- Local immutable staging run `local-wo03-complete` passed Administrator bootstrap, project create/list/update/archive, owner-scoped audit read, session revocation attribution, controlled worker failure, recovery, and unchanged image identity.
- Candidate image IDs: API `sha256:8d9ff0ae5ca5a7e49507b8946a26641d677ecfa3d9bca85550a5fd801a6a4ccf`; web `sha256:826b5e1fb0d9a360d63eb8df5b0def74703d77b505ceaf6c562e9b7390615f86`; worker `sha256:0e3c8a08f1cd5885ec9fe5074e4b75dbd5b1108b4f3120f399667dc076fa5615`.
- Hosted CI run `36900029244` passed contract/static, architecture, security/supply-chain, full PostgreSQL-backed tests, deterministic resource limits, package/SBOM, isolated staging, controlled failure, recovery, and evidence-bundle stages on commit `478146c`.
- The implementation conformance review found no unresolved scope, architecture, security, project-isolation, safe-error, or audit-attribution discrepancy. No capability acceptance is claimed.

## Definition of Done

- The four acceptance criteria and TST-WO-CAP-01-03 pass against the identified implementation snapshot
- Any assigned catalogue-listed BDD execution and workorder-owned manual/security evidence are complete
- Applicable ARCH/SEC checks, migrations, documentation, result reporting, and EXTENDED implementation review are complete
- Remaining capability-level execution stays explicitly owned by WO-CAP-01-05

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-01 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-00
- Required workorders: WO-CAP-01-04, WO-CAP-01-02
- Downstream acceptance owner: WO-CAP-01-05
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
