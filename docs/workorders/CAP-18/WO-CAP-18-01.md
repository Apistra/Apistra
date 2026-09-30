# WO-CAP-18-01 — Define commercial entitlement model

Version: 0.6-draft
Status: DRAFT
Status reason: CAP-00 and the named workorder prerequisites are not yet satisfied
Implementation state: NOT STARTED
Evidence state: NOT EXECUTED
Approval state: NOT APPROVED
Capability: [CAP-18](../../capabilities/CAP-18-commercial-operations-and-optional-managed-service.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-017, REQ-031
- Process: PRC-14
- Capability contract: ../../capabilities/CAP-18-commercial-operations-and-optional-managed-service.md
- CI test group: TST-WO-CAP-18-01
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder
- Delivery class: contract-definition
- Owned verification group: TST-WO-CAP-18-01
- Specification revision: 0.6-draft; earlier evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects authorization, secrets, delivery_control, and irreversible_data. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Define commercial entitlement model”; all other baseline behavior remains unchanged.

## Context and current behavior

Current evidence does not establish this 0.6 workorder result. Existing code and prior CAP-00 evidence are an observed baseline only; they do not define the expected behavior. Before READY, the readiness review must record current repository paths, public/persisted contracts, consumers, relevant configuration/identity boundaries, and any contradicting behavior.

## Target result

A versioned, review-approved definition for commercial entitlement model provides unambiguous valid, invalid, compatibility, ownership, and failure semantics to every named consumer.

## Prerequisites

- Dependencies: CAP-01 and legal/production approvals
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Define the canonical versioned schema or policy, invariants, ownership, lifecycle, compatibility, unknown-version behavior, safe errors, and consumer obligations.
- Retain valid, boundary, invalid, and incompatible examples as fixtures where machine validation is possible.
- Update traceability and only those ADR/ARCH/SEC references changed by this contract.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Path authority: [Business Workorder Repository Path Contract](../../planning/12-repository-path-contract.md).

Repository observation: 2026-09-30 at commit `be7e84d`. EXISTING means the literal path was observed at that baseline; PLANNED means this workorder may create or use that exact path only after every READY prerequisite is satisfied. A path label is not implementation evidence.

Observed existing paths within the bounded change area:

- EXISTING: `docs/workorders/CAP-18/WO-CAP-18-01.md`
- EXISTING: `docs/capabilities/CAP-18-commercial-operations-and-optional-managed-service.md`
- EXISTING: `CHANGELOG.md`
- EXISTING: `backend/tests/contract/`
- EXISTING: `contracts/openapi/`
- EXISTING: `contracts/events/`
- EXISTING: `LICENSE`
- EXISTING: `NOTICE`
- EXISTING: `COMMERCIAL-LICENSE.md`
- EXISTING: `LICENSES/`
- EXISTING: `docs/operations/`

Planned additions to the bounded change area after READY:

- PLANNED: `backend/tests/contract/cap_18/`

Workorder-class boundary: Contract definition only; no product runtime behaviour is authorised. Changes stay within the listed schema, SDK, contract-test, governance, and directly affected documentation paths.

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

- Rules: ARCH-003, ARCH-005, ARCH-012
- Applicability: the versioned boundary/policy defined by this workorder; runtime-only rules remain with consuming implementations.
- ADRs/patterns: ADR-002 through ADR-005, ADR-009 through ADR-011, ADR-013, ADR-017, ADR-018 plus production ADRs
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-002, SEC-007, SEC-012, SEC-015
- Applicability: the versioned boundary/policy defined by this workorder; runtime-only rules remain with consuming implementations.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. The contract has one canonical representation, explicit version semantics, ownership, invariants, and unknown-version behavior.
2. At least one valid, boundary, malformed, incompatible, and unauthorised example has an objective expected result.
3. Every named consumer can implement against the contract without choosing a new product, architecture, security, or compatibility rule.
4. A qualified review approves the contract and its impact before dependent implementation becomes READY.

## Acceptance examples and test oracles

- **Positive oracle:** A supported example of commercial entitlement model validates and round-trips without semantic loss.
- **Negative oracle:** A malformed, incompatible, unauthorised, or unknown-version example of commercial entitlement model is rejected before any consumer mutation.
- **Boundary oracle:** Minimum and maximum supported versions, sizes, counts, ownership scopes, and compatibility edges have explicit valid or rejected outcomes.
- **Evidence binding:** every executed result identifies specification revision 0.6, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-017, REQ-031, process PRC-14, and cited architecture/security/design contracts.
- Positive expectation: A supported example of commercial entitlement model validates and round-trips without semantic loss.
- Counterexample: A malformed, incompatible, unauthorised, or unknown-version example of commercial entitlement model is rejected before any consumer mutation.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-18-01: schema/policy validation and valid/boundary/invalid/unknown-version fixtures in CI-TS-01 or the owning contract stage.
- Architecture dependency review for every consumer and applicable ARCH rule.
- Security review for ownership, identity, secret, egress, and failure semantics named by applicable SEC rules.
- No product BDD or manual UI test is assigned until a dependent workorder exposes behavior.

## BDD and manual tests

No BDD or manual case is required for a contract with no independently observable journey. Behavioral consumers receive their own stable IDs; the contract fixtures remain this workorder's evidence.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

No staging acceptance is owned unless this workorder explicitly changes a deployed contract reader. The final capability gate verifies the contract through its consuming behavior.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- Canonical contract, fixtures, compatibility policy, and consumer list are approved
- Assigned contract, architecture, and security checks pass
- Dependent workorders reference the exact contract revision
- No runtime behavior or external resource is represented as implemented

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-18 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-01 and legal/production approvals
- Required workorders: none within this capability
- Downstream acceptance owner: WO-CAP-18-09
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
