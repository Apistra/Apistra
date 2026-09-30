# WO-CAP-05-03 — Review, refine, and approve visual design references

Version: 0.6-draft
Status: DRAFT
Status reason: CAP-00 and the named workorder prerequisites are not yet satisfied
Implementation state: NOT STARTED
Evidence state: NOT EXECUTED
Approval state: NOT APPROVED
Capability: [CAP-05](../../capabilities/CAP-05-workflow-authoring-and-publication.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-008, REQ-009, REQ-018
- Process: PRC-03
- Capability contract: ../../capabilities/CAP-05-workflow-authoring-and-publication.md
- CI test group: TST-WO-CAP-05-03
- Softwaretest.it mapping: NOT PUBLISHED; assigned to the capability test-definition workorder
- Delivery class: design-decision
- Owned verification group: TST-WO-CAP-05-03
- Specification revision: 0.6-draft; earlier evidence requires explicit change-impact validation before reuse

## Risk profile and escalation

EXTENDED applies because this workorder affects tenant_isolation and architecture_boundary. Impact is potentially system-wide, uncertainty remains until the named contracts and paths are observed, and unsafe state or external effects may not be simply reversible.

Stop and reassess the profile, specification, tests, and dependent evidence if implementation reveals a new identity/project boundary, data migration, external permission, destructive or uncertain effect, provider limitation, architecture boundary, or material scope increase. Time pressure or a green partial test does not justify de-escalation.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Decisions: ../../planning/02-decision-register.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery, tests, design: ../../planning/05-delivery-ci-contract.md through ../../planning/07-design-contract.md
- Delta: deliver only “Review, refine, and approve visual design references”; all other baseline behavior remains unchanged.

## Context and current behavior

Current evidence does not establish this 0.6 workorder result. Existing code and prior CAP-00 evidence are an observed baseline only; they do not define the expected behavior. Before READY, the readiness review must record current repository paths, public/persisted contracts, consumers, relevant configuration/identity boundaries, and any contradicting behavior.

## Target result

Product-owner-approved maintainable and rendered references define the workflow-authoring interaction before UI implementation starts.

## Prerequisites

- Dependencies: CAP-01 through CAP-04 and GATE-DES-01
- GATE-CAP00-DONE and Softwaretest.it publishing readiness for business implementation
- Approved expectation review for this specification revision
- Approved ADRs, security decisions, and design references actually used by this workorder

## Scope

- Review and refine workflow editor information architecture, desktop/responsive layouts, components, interaction states, keyboard/focus behavior, reduced motion, and accessibility annotations.
- Preserve source and rendered assets for every approved reference and viewport.
- Record product-owner approval or specific rejected/open items; do not implement the UI.

## Non-goals and prohibited side effects

- No unrelated refactor, dependency, connector, node type, role, production target, or automatic deployment
- No secret values in definitions, logs, exports, fixtures, screenshots, or evidence
- No weakening of architecture tests, required CI stages, security rules, or prior accepted behavior
- No new repository path or module boundary before it is reconciled with the observed ADR-019 layout

## Allowed changes

Path authority: [Business Workorder Repository Path Contract](../../planning/12-repository-path-contract.md).

Repository observation: 2026-09-30 at commit `be7e84d`. EXISTING means the literal path was observed at that baseline; PLANNED means this workorder may create or use that exact path only after every READY prerequisite is satisfied. A path label is not implementation evidence.

Observed existing paths within the bounded change area:

- EXISTING: `docs/workorders/CAP-05/WO-CAP-05-03.md`
- EXISTING: `docs/capabilities/CAP-05-workflow-authoring-and-publication.md`
- EXISTING: `CHANGELOG.md`
- EXISTING: `docs/planning/07-design-contract.md`
- EXISTING: `docs/visuals/design/`
- EXISTING: `docs/visuals/generate_visuals.py`
- EXISTING: `images/`

Planned additions to the bounded change area after READY:



Workorder-class boundary: Design decision only; no product runtime implementation is authorised. Changes stay within maintainable design sources, rendered references, the design contract, and directly affected indexes.

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

This UI workorder additionally requires an approved design reference, named viewports, full interaction states, accessibility evidence, and manual UI/UX cases.

## ARCH rules and pattern limits

- Rules: ARCH-006, ARCH-012
- Applicability: canonical workflow representation, stable UI contracts, project-aware states, and traceable approval.
- ADRs/patterns: ADR-001, ADR-003 through ADR-005, ADR-011 through ADR-018
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-015
- Applicability: canonical workflow representation, stable UI contracts, project-aware states, and traceable approval.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. Workflow editor references cover normal, loading, empty, success, validation error, save error, conflict, permission, disabled, and recovery states.
2. Desktop and responsive behavior, keyboard order, focus restoration, labels, contrast intent, zoom, and reduced motion are explicitly specified.
3. Manual UI/UX cases map every required state and approved viewport to an observable result.
4. The product owner approves the exact source/rendered revision; agent self-approval is invalid.

## Acceptance examples and test oracles

- **Positive oracle:** The approved source and rendered workflow-editor references cover every named state and viewport with traceable accessibility annotations.
- **Negative oracle:** A missing error/conflict/permission state, inaccessible interaction, source/render mismatch, or absent product-owner approval blocks UI implementation READY.
- **Boundary oracle:** The narrowest and widest approved viewports, 200% text zoom, keyboard-only use, reduced motion, and longest supported labels remain operable.
- **Evidence binding:** every executed result identifies specification revision 0.6, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-008, REQ-009, REQ-018, process PRC-03, and cited architecture/security/design contracts.
- Positive expectation: The approved source and rendered workflow-editor references cover every named state and viewport with traceable accessibility annotations.
- Counterexample: A missing error/conflict/permission state, inaccessible interaction, source/render mismatch, or absent product-owner approval blocks UI implementation READY.
- Before READY, an independent derivation and comparison must record reviewer, revision, discrepancies, decisions, and human confirmation of critical expectations.

## Required tests

- TST-WO-CAP-05-03: design-reference inventory, source/render parity, link, and required-state validation.
- Independent accessibility/design review against DSN references and WCAG 2.2 AA requirements.
- Manual UI/UX definitions are prepared under WO-CAP-05-08; no implementation test is invented here.

## BDD and manual tests

No automated BDD execution is owned. The design-review case belongs to `MTP-PRC-03`; WO-CAP-05-08 must allocate and publish its concrete `MT-PRC-03-NNN` ID and atomic steps before dependent UI work becomes READY.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

No application candidate is deployed. Approval evidence binds the exact design-source and rendered-reference hashes consumed later by UI workorders.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt

## Definition of Done

- Maintainable sources and rendered references cover required states and viewports
- Accessibility and manual UI/UX mappings are independently reviewed
- Product-owner approval binds the exact revision
- No UI implementation or capability acceptance is claimed

## Workorder completion versus capability acceptance

DONE proves only this integrated result. CAP-05 remains unaccepted until every workorder is DONE, the unchanged candidate passes the full scope matrix on staging, required manual tests and Softwaretest.it reporting are confirmed, and an authorised human accepts the capability.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-01 through CAP-04 and GATE-DES-01
- Required workorders: WO-CAP-05-01
- Downstream acceptance owner: WO-CAP-05-09
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
