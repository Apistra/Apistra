# WO-CAP-02-02 — Implement model and embedding endpoint catalogue

Version: 0.9-ready
Status: READY
Status reason: the bounded implementation and local automated evidence exist on `feature/cap02-endpoint-catalogue`; protected CI, independent implementation review, merge, and human workorder approval remain required before DONE
Implementation state: IMPLEMENTED ON FEATURE BRANCH; REVIEW AND PROTECTED MERGE PENDING
Evidence state: LOCAL STATIC, ARCHITECTURE, CONTRACT, BACKEND, FRONTEND, MIGRATION, POSTGRESQL, AND COVERAGE GATES VERIFIED; PROTECTED CI PENDING
Approval state: INDEPENDENT IMPLEMENTATION REVIEW REQUIRED; HUMAN WORKORDER APPROVAL NOT YET GIVEN
Capability: [CAP-02](../../capabilities/CAP-02-secrets-endpoints-agents-tools-and-limits.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-003, REQ-004, REQ-005, REQ-013, REQ-014
- Process: PRC-01
- Capability contract: ../../capabilities/CAP-02-secrets-endpoints-agents-tools-and-limits.md
- CI test group: TST-WO-CAP-02-02
- Softwaretest.it mapping: PUBLISHED AND VERIFIED by WO-CAP-02-06; execution remains with WO-CAP-02-07
- Delivery class: implementation
- Owned verification group: TST-WO-CAP-02-02
- Specification revision: 0.9-ready; local evidence is bound to the current feature-branch tree and must be replaced by protected candidate evidence after merge

## Risk profile and escalation

EXTENDED applies because this workorder affects secrets, authorization, and architecture_boundary. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Implement model and embedding endpoint catalogue”; all other baseline behavior remains unchanged.

## Context and current behavior

CAP-00 and CAP-01 are accepted baselines. WO-CAP-02-06 published and verified
BDD-ENDPOINT-001 and MT-PRC-01-009. WO-CAP-02-01 is DONE on protected `test` at
`dfa8319e7eb93c6ef3bd15c0ec3918a2bdd1ef9a`. The feature branch now implements
the provider-neutral endpoint domain/application/port boundary, memory and
PostgreSQL adapters, a versioned migration and OpenAPI contract, authenticated
project-scoped HTTP routes, safe audit projection, DSN-005, and focused tests.
Save performs no DNS or network operation. Explicit testing resolves and
approves every destination address before credential release, pins the selected
address, rejects redirects, bounds time and response size, and confirms the
configured model through the read-only OpenAI-compatible `/models` operation.
The approved readiness review remains the expectation, architecture, security,
design, and path authority. This is local implementation evidence, not DONE or
capability acceptance.

## Target result

The capability exposes model and embedding endpoint catalogue as one integrated, versioned, project-scoped behavior through its declared application/public boundary, with safe failure and evidence for downstream work.

## Prerequisites

- Dependencies: CAP-01
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Implement only model and embedding endpoint catalogue, including its domain invariants, application use case, declared public/schema boundary, required adapter behavior, persistence/migration delta, safe errors, audit/observability, and focused documentation.
- Preserve existing capability boundaries and use only approved contracts/ADRs; no adjacent catalogue item is included.
- Add the positive, negative, boundary, compatibility, architecture, and security tests owned by this workorder.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Path authority: [Business Workorder Repository Path Contract](../../planning/12-repository-path-contract.md).

Repository observation: 2026-09-30 at commit `be7e84d`.

Readiness review observation: 2026-10-04 at commit `d83810d181374171abc7118b37a5090b6c71bb7f`. EXISTING means the literal path was observed at the repository path-contract baseline and rechecked for this readiness revision; PLANNED means this workorder may create or use that exact path only after every READY prerequisite is satisfied. A path label is not implementation evidence.

Observed existing paths within the bounded change area:

- EXISTING: `docs/workorders/CAP-02/WO-CAP-02-02.md`
- EXISTING: `docs/capabilities/CAP-02-secrets-endpoints-agents-tools-and-limits.md`
- EXISTING: `CHANGELOG.md`
- EXISTING: `backend/src/apistra/modules/`
- EXISTING: `backend/src/apistra/entrypoints/api/composition.py`
- EXISTING: `backend/src/apistra/entrypoints/worker/composition.py`
- EXISTING: `apps/web/src/features/`
- EXISTING: `backend/tests/unit/`
- EXISTING: `backend/tests/component/`
- EXISTING: `backend/tests/contract/`
- EXISTING: `backend/tests/integration/`
- EXISTING: `contracts/openapi/`
- EXISTING: `contracts/events/`

Planned additions to the bounded change area after READY:

- EXISTING: `backend/src/apistra/modules/catalog/`
- PLANNED: `backend/src/apistra/modules/agents/`
- PLANNED: `backend/src/apistra/modules/policies/`
- EXISTING: `apps/web/src/features/catalog/`
- PLANNED: `apps/web/src/features/agents/`
- PLANNED: `apps/web/src/features/policies/`
- EXISTING: `backend/tests/unit/cap_02/`
- EXISTING: `backend/tests/component/cap_02/`
- EXISTING: `backend/tests/contract/cap_02/`
- EXISTING: `backend/tests/integration/cap_02/`
- EXISTING: `tests/bdd/features/cap_02/`
- EXISTING: `backend/src/apistra/platform/database/migrations/cap_02/`

Implemented paths observed on the feature branch:

- `backend/src/apistra/modules/catalog/domain/endpoints.py`
- `backend/src/apistra/modules/catalog/application/endpoints.py`
- `backend/src/apistra/modules/catalog/ports/endpoints.py`
- `backend/src/apistra/modules/catalog/adapters/endpoint_memory.py`
- `backend/src/apistra/modules/catalog/adapters/endpoint_postgres.py`
- `backend/src/apistra/modules/catalog/adapters/probe.py`
- `backend/src/apistra/entrypoints/api/endpoints.py`
- `backend/src/apistra/platform/database/migrations/cap_02/002_model_endpoints.sql`
- `contracts/openapi/cap02-endpoints.openapi.json`
- `apps/web/src/features/catalog/endpoints.tsx`
- `apps/web/src/features/catalog/internal/endpoint-client.ts`
- `apps/web/src/app/projects/[projectId]/endpoints/page.tsx`
- focused tests below `backend/tests/{unit,component,contract,integration}/cap_02/`
- `apps/web/src/features/catalog/endpoints.test.ts`

Workorder-class boundary: Product implementation only inside the listed module, feature, contract, focused-test, optional migration, composition-root, and directly affected documentation paths.

Architecture path gate: ADR-019 top-level roots are DECIDED; planned child paths still require this workorder's expectation and architecture review before READY.

Path boundary: The EXISTING and PLANNED paths together form the upper bound after READY, not an instruction to touch every path. While this workorder is DRAFT/BLOCKED it authorises no implementation. An unlisted path, a new top-level root, a private cross-module import, or cross-module table access is a stop condition requiring observed impact, specification revision, and review.

## Stop conditions

- CAP-00 or CAP-01 acceptance is invalidated, or another named prerequisite is not satisfied
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

UI scope is DSN-005 from design revision 0.4 after its explicit product approval; no other page is authorised.

## ARCH rules and pattern limits

- Rules: ARCH-002, ARCH-003, ARCH-005, ARCH-009, ARCH-011, ARCH-012
- Applicability: the named implementation result; capability-wide rules not listed remain owned by their specific workorders or final acceptance.
- ADRs/patterns: ADR-002 through ADR-004, ADR-009, ADR-010, ADR-013, ADR-014, ADR-017 through ADR-019, ADR-024, ADR-025; ADR-005 only if a real lifecycle requires it
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-002, SEC-004, SEC-007, SEC-012, SEC-015, SEC-016
- Applicability: the named implementation result; capability-wide rules not listed remain owned by their specific workorders or final acceptance.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. An Administrator registers and validates versioned model and embedding endpoints with explicit capabilities and protected credentials.
2. Unsupported capability, invalid configuration, or unreachable endpoint produces a safe actionable result without persisting a usable endpoint.
3. All state changes are project-scoped, version/conflict checked where mutable, idempotent where redelivery is possible, and attributable through safe audit/diagnostic correlations.
4. Every public or persisted delta has a versioned contract and tested migration/compatibility behavior, or explicit evidence that no such delta exists.

## Acceptance examples and test oracles

- **Positive oracle:** An Administrator registers and validates versioned model and embedding endpoints with explicit capabilities and protected credentials.
- **Negative oracle:** Unsupported capability, invalid configuration, or unreachable endpoint produces a safe actionable result without persisting a usable endpoint.
- **Boundary oracle:** Declared empty, minimum, maximum, timeout, concurrency, version, conflict, and ownership boundaries applicable to this result produce explicit documented outcomes.
- **Evidence binding:** every executed result identifies specification revision 0.9-ready, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-003, REQ-004, REQ-005, REQ-013, REQ-014, process PRC-01, and cited architecture/security/design contracts.
- Positive expectation: An Administrator registers and validates versioned model and embedding endpoints with explicit capabilities and protected credentials.
- Counterexample: Unsupported capability, invalid configuration, or unreachable endpoint produces a safe actionable result without persisting a usable endpoint.
- The CAP-02 readiness review records the independent derivation/comparison and product-owner confirmation for this endpoint slice against the approved baseline. Any changed endpoint behavior, provider boundary, egress policy, credential flow, or test oracle invalidates that review and returns this workorder to DRAFT/BLOCKED.

## Required tests

- TST-WO-CAP-02-02: focused unit/component tests for the named invariants, state transitions, boundary values, and safe error taxonomy.
- Canonical BDD coverage: BDD-ENDPOINT-001; WO-CAP-02-06 owns the exact scenario definition and traceability before READY.
- Contract and compatibility fixtures for each changed public/persisted schema, including unknown-version rejection.
- Architecture and security tests for the listed ARCH/SEC rules, including own-project success and foreign/anonymous/revoked denial where access exists.
- Capability regression selected by recorded change impact; WO-CAP-02-07 still owns the final complete unchanged-candidate matrix.

## BDD and manual tests

WO-CAP-02-06 defined, published, and exactly read back BDD-ENDPOINT-001 and manual case MT-PRC-01-009. Execution remains with WO-CAP-02-07.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

This workorder produces candidate-bound evidence but does not accept the capability. WO-CAP-02-07 owns deployment of the exact complete candidate, full staging matrix, recovery, manual execution, and human acceptance.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

### Current feature-branch evidence

- Python formatting and Ruff, strict mypy, selected flake8 conventions,
  Import Linter, TypeScript type checking, TypeScript architecture,
  cyclomatic-complexity, and repository-contract gates passed locally.
- The complete backend matrix passed with `125 passed` and 90.38% aggregate
  coverage against an isolated PostgreSQL 17.6 instance; the temporary test
  container was removed after the run.
- The web matrix passed with `19 passed`, 96.92% line coverage, and 100%
  function coverage.
- PostgreSQL migration and endpoint-store integration tests passed, including
  idempotent creation, optimistic probe versioning, audit persistence, and the
  secret-reference foreign key.
- Credential-safe tests prove offline save, deny-before-decrypt, all-answer DNS
  policy, link-local/metadata denial, bounded provider reads, redirect denial,
  timeout normalization, exact model discovery, and safe normalized outcomes.
- These local results do not replace protected CI, immutable candidate/staging
  evidence, independent implementation review, or human approval.

## Definition of Done

- The four acceptance criteria and TST-WO-CAP-02-02 pass against the identified implementation snapshot
- Any assigned catalogue-listed BDD execution and workorder-owned manual/security evidence are complete
- Applicable ARCH/SEC checks, migrations, documentation, result reporting, and EXTENDED implementation review are complete
- Remaining capability-level execution stays explicitly owned by WO-CAP-02-07

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-02 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-01
- Required workorders: WO-CAP-02-06, WO-CAP-02-01
- Downstream acceptance owner: WO-CAP-02-07
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
