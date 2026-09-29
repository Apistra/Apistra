# WO-CAP-15-01 — Define versioned role and permission model

Version: 0.4-draft
Status: DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
Capability: [CAP-15](../../capabilities/CAP-15-role-based-administration-and-enterprise-identity.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-028
- Process: PRC-11
- Capability contract: ../../capabilities/CAP-15-role-based-administration-and-enterprise-identity.md
- CI test group: TST-WO-CAP-15-01
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder

## Risk profile and escalation

EXTENDED applies because the product plan crosses architecture boundaries and may affect authorization, tenant isolation, secrets, delivery control, or durable state. Stop and reassess if implementation reveals a new data migration, external permission, architecture boundary, irreversible effect, or material scope increase.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Define versioned role and permission model”; all other baseline behavior remains unchanged.

## Context and current behavior

The capability result is not implemented. Existing CAP-00 health behavior is not evidence of this workorder.

## Target result

Define versioned role and permission model is available as one integrated, reviewable result consumed by the remaining CAP-15 workorders. It must not silently implement adjacent catalogue items.

## Prerequisites

- Dependencies: CAP-01
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Implement or specify exactly: Define versioned role and permission model.
- Add or update its public/schema contract, focused tests, safe diagnostics, audit/observability behavior, and required documentation.
- Preserve project isolation, offline-capable operation, and the feature → test → staging → main promotion contract.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Resolve exact paths during readiness review from the observed repository. Changes are limited to the owning backend module, its public contract, required API/worker/web adapter, language-neutral contracts, focused tests, fixtures, and directly affected documentation. Cross-module table access and private imports are forbidden.

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

- Rules: ARCH-001 through ARCH-005, ARCH-011, ARCH-012
- ADRs/patterns: ADR-002 through ADR-005, ADR-009, ADR-010, ADR-013 through ADR-015, ADR-017, ADR-018
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-008, SEC-009, SEC-012, SEC-015
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. The contract is versioned, schema-valid, and identifies compatibility and unknown-version behavior.
2. Allowed and forbidden examples plus boundary cases are retained as executable fixtures where automatable.
3. All consuming workorders can use the contract without inventing a product, architecture, or security decision.
4. A qualified review approves any new architecture decision before dependent implementation becomes READY.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-028, process PRC-11, and cited architecture/security/design contracts.
- Example: the named result succeeds for an authorised actor using valid project-owned, versioned input.
- Counterexample: equivalent foreign-project, stale, malformed, revoked, duplicated, or policy-forbidden input does not succeed and leaks no protected data.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-15-01 unit/component tests for rules, boundaries, state, and error taxonomy
- Contract tests for every changed public/schema boundary and unknown-version behavior
- Architecture tests for the applicable ARCH rules, including retained forbidden fixtures
- Security tests for applicable SEC rules and actual identities/configuration
- Regression tests selected by documented change-impact analysis; the final capability gate runs the full scope matrix

## BDD and manual tests

BDD and manual case IDs are assigned by the capability test-definition workorder before implementation READY. Manual process/UI cases are independent from BDD, start at sign-in, use verified synthetic users/data, and contain atomic role-prefixed steps. This workorder cannot be DONE if its own assigned test execution remains outstanding.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

This workorder supplies candidate-bound evidence to the final capability acceptance workorder; it does not itself approve deployment or production.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- Acceptance criteria and this workorder’s assigned tests pass
- Applicable ARCH/SEC rules are evidenced with no unapproved blocking finding
- Documentation and contracts are current; evidence is candidate-bound and reported
- EXTENDED independent implementation review is accepted
- Remaining capability-level tests are still explicitly owned by the final acceptance workorder

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-15 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

Upstream: CAP-01. Downstream: the next numbered CAP-15 workorder and ultimately the final staging-acceptance workorder. No downstream item may infer completion from this file alone.

