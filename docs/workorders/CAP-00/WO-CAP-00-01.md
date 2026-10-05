# WO-CAP-00-01 — Establish repository governance and planning checks

Version: 0.7-done
Status: DONE
Status reason: revision 0.6 repository, governance, and protected hosted checks passed on the accepted candidate
Implementation state: IMPLEMENTED
Evidence state: VERIFIED — live branch protection and the complete protected test workflow are recorded
Approval state: REVIEWED — CAP-00 product-owner review recorded 2026-09-30 and reused after non-behavioural reporting repairs
Capability: [CAP-00](../../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-019, REQ-020
- Process: PRC-07
- Capability contract: ../../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md
- CI test group: TST-WO-CAP-00-01
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder
- Delivery class: repository-governance
- Owned verification group: TST-WO-CAP-00-01
- Specification revision: 0.7-done earlier evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects delivery_control and architecture_boundary. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Establish repository governance and planning checks”; all other baseline behavior remains unchanged.

## Context and current behavior

CAP-00 implementation and earlier hosted evidence exist against prior workorder revisions. This 0.6 revision strengthens the execution and evidence contract without claiming a new implementation result. A documented change-impact review must identify which prior evidence remains valid and which checks or approvals must be repeated.

## Target result

The approved repository governance and planning checks package states enforceable responsibilities, boundaries, processes, and unresolved decisions without claiming legal, operational, or technical capabilities that are not evidenced.

## Prerequisites

- Dependencies: None
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Define the bounded governance documents, responsible roles, decision rights, review triggers, compatibility with existing licences/contracts, and required operational evidence.
- Reconcile contradictions across repository policy, licensing, security, delivery, support, and public statements.
- Obtain the qualified human/legal review required by the subject; do not create runtime behavior.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Observed path scope for this completed bootstrap slice: .github/, docs/, CONTRIBUTING.md, SECURITY.md, and tools/contracts/. Any change outside these paths requires an explicit scope/impact update before work continues.

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

- Rules: ARCH-010, ARCH-013, ARCH-014
- Applicability: repository/engineering isolation, acyclic structure, local-first delivery, supply chain, and evidence confidentiality.
- ADRs/patterns: ADR-017 and ADR-019
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-011, SEC-012, SEC-013
- Applicability: repository/engineering isolation, acyclic structure, local-first delivery, supply chain, and evidence confidentiality.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. Every public or operator-facing claim identifies its authority, scope, effective revision, and unresolved limitations.
2. Conflicting licensing, contribution, support, warranty, privacy, security, or release statements are resolved or explicitly blocking.
3. Required roles, decision rights, escalation, review triggers, and evidence retention are actionable.
4. Qualified human/legal approval is recorded where required; automated checks do not substitute for it.

## Steering criterion evidence

- WO-CAP-00-01-AC-01: status=PASSED; due_now=true; gate=WO-CAP-00-01 completion; reason=The revision 0.6 governance package and protected planning checks identify the authority, scope, revision, and limitations of repository-facing claims.
- WO-CAP-00-01-AC-02: status=PASSED; due_now=true; gate=WO-CAP-00-01 completion; reason=The reviewed governance and licensing sources explicitly resolve the applicable public statements or retain unresolved matters as named gates; the protected repository checks passed.
- WO-CAP-00-01-AC-03: status=PASSED; due_now=true; gate=WO-CAP-00-01 completion; reason=The accepted governance package records roles, decision rights, escalation, review triggers, and evidence retention; protected run 36875393087 revalidated its repository checks.
- WO-CAP-00-01-AC-04: status=PASSED; due_now=true; gate=WO-CAP-00-01 completion; reason=The product-owner review was recorded on 2026-09-30; no separate legal certification was required by the approved CAP-00 scope, and this result does not claim one.

## Acceptance examples and test oracles

- **Positive oracle:** The approved repository governance and planning checks package makes only source-backed claims and names roles, decisions, limitations, and review triggers.
- **Negative oracle:** An unsupported legal/support/security/release claim, unresolved contradiction, or missing qualified approval remains visibly blocking.
- **Boundary oracle:** Every named audience, distribution mode, support boundary, licence case, and approval trigger is either covered or explicitly out of scope.
- **Evidence binding:** every executed result identifies specification revision 0.6, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-019, REQ-020, process PRC-07, and cited architecture/security/design contracts.
- Positive expectation: The approved repository governance and planning checks package makes only source-backed claims and names roles, decisions, limitations, and review triggers.
- Counterexample: An unsupported legal/support/security/release claim, unresolved contradiction, or missing qualified approval remains visibly blocking.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-00-01: repository policy, link, version, contradiction, and required-section validation in CI-TS-01.
- Structured qualified review of legal/security/operations claims and their source authority.
- Negative fixture or review case proving unsupported claims and absent approvals remain visible.
- No BDD or manual product test is invented for a documentation-only result.

## BDD and manual tests

BDD and manual product cases are not applicable to the governance artifact itself. Any operational procedure introduced by it must receive a separate executable test/workorder before use.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

No product deployment is owned. Published documentation must remain bound to the repository revision and cannot constitute production authorisation.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- Governance documents are internally consistent, source-backed, and qualified-review approved
- Required decisions, roles, escalation, and limitations are explicit
- Repository checks pass and affected downstream contracts are updated
- No legal approval, support promise, certification, or production capability is invented

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-00 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: None
- Required workorders: none within this capability
- Downstream acceptance owner: WO-CAP-00-07
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
