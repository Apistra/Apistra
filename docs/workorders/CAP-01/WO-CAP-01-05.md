# WO-CAP-01-05 — Accept CAP-01 on local staging

Version: 0.9-done
Status: DONE
Status reason: the exact fix tree passed local-staging acceptance and protected test CI; all three linked defects are CLOSED/FIXED after successful direct retests, and the product owner accepted CAP-01 on 2026-10-04
Implementation state: COMPLETE
Evidence state: VERIFIED — candidate, fixtures, protected CI, manual runs, direct retests, and defect closure reconciled
Approval state: REVIEWED AND HUMAN ACCEPTED — production approval remains ungranted
Capability: [CAP-01](../../capabilities/CAP-01-installation-and-isolated-project-administration.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-001, REQ-002, REQ-016, REQ-017
- Process: PRC-01
- Capability contract: ../../capabilities/CAP-01-installation-and-isolated-project-administration.md
- CI test group: TST-WO-CAP-01-05
- Softwaretest.it mapping: DEFINITIONS PUBLISHED; EXECUTION AND DIRECT DEFECT-RETEST EVIDENCE VERIFIED WITH DOCUMENTED PLATFORM EXCEPTION
- Delivery class: capability-acceptance
- Owned verification group: TST-WO-CAP-01-05
- Specification revision: 0.9-done; acceptance evidence is bound to the candidate and platform state recorded below

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

WO-CAP-01-01 through WO-CAP-01-04 are DONE, including authenticated
Softwaretest.it definition publication and read-back. Candidate
`e522266b8d113ddd8e6807669fb3f3abf88e3eae` was run in isolated local staging as
`cap01-retest-e522266-01`. PR #25 merged that exact tree to protected `test` as
`e348ee5f3b6ef8f11fbcc37e417093540176c66d`; protected run `37192774502` passed
all six jobs, including candidate packaging, staging/recovery, Steering,
definition publication, and result reporting. The product owner reviewed the
code and confirmed successful direct retests. Softwaretest.it reports
APISTRA-D0001 through APISTRA-D0003 as CLOSED/FIXED at revision 5.

Softwaretest.it's alternate direct defect-retest path does not create the same
RetestDocument/run status as the normal repeat workflow. Consequently the unused
second APISTRA-TC-000006 run remains `NOT_STARTED`. The product owner explicitly
decided on 2026-10-04 that the successful direct retests plus closure of every
linked defect are authoritative for this acceptance. The stale display is
retained as a documented platform exception and is not rewritten as a passed
run.

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

Path authority: [Business Workorder Repository Path Contract](../../planning/12-repository-path-contract.md).

Repository observation: 2026-09-30 at commit `be7e84d`. EXISTING means the literal path was observed at that baseline; PLANNED means this workorder may create or use that exact path only after every READY prerequisite is satisfied. A path label is not implementation evidence. Current protected-baseline integration is recorded separately in the context above.

Observed existing paths within the bounded change area:

- EXISTING: `docs/workorders/CAP-01/WO-CAP-01-05.md`
- EXISTING: `docs/capabilities/CAP-01-installation-and-isolated-project-administration.md`
- EXISTING: `CHANGELOG.md`
- EXISTING: `deploy/compose/`
- EXISTING: `backend/tests/unit/`
- EXISTING: `tools/staging/`
- EXISTING: `docs/testing/manual/PRC-01/`

Planned additions to the bounded change area after READY:

- PLANNED: `tests/manual/CAP-01/`
- PLANNED: `artifacts/acceptance/CAP-01/`

Workorder-class boundary: Capability acceptance only; no feature implementation is authorised. Changes stay within staging verification, acceptance definitions/evidence, and directly affected documentation.

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

- Rules: ARCH-002, ARCH-005, ARCH-008, ARCH-009, ARCH-010, ARCH-011, ARCH-012, ARCH-014, ARCH-015
- Applicability: the full capability envelope because this workorder owns unchanged-candidate acceptance.
- ADRs/patterns: verifies the approved CAP-01 pattern union from WO-CAP-01-01 through WO-CAP-01-04 and introduces no new implementation pattern
- Only ADRs approved for the exact scope are binding; proposed or pending decisions keep dependent implementation BLOCKED.
- Architecture tests require an allowed fixture, a forbidden counterexample, actual source-scope discovery, and a non-empty result.

## SEC rules and safe test conditions

- Rules: SEC-001, SEC-003, SEC-004, SEC-006, SEC-007, SEC-009, SEC-011, SEC-012, SEC-015, SEC-016
- Applicability: the full capability envelope because this workorder owns unchanged-candidate acceptance.
- Tests use only authorised local/staging targets and synthetic project-scoped data.
- Positive own-project and negative foreign-project/anonymous/revoked cases are mandatory where access exists.
- Egress, secrets, destructive operations, cost, concurrency, and recovery limits follow the security baseline.

## Acceptance criteria

1. Every prerequisite workorder is DONE and no blocking or expired exception remains.
2. The complete required matrix passes on one unchanged commit/candidate with current suite and input fingerprints.
3. The same digests are staged manually; migration, health, smoke, observability, controlled failure, recovery, and all assigned manual cases pass with confirmed reporting.
4. An authorised human accepts the exact capability/candidate/environment evidence package; no production approval is inferred.

## Steering criterion evidence

- WO-CAP-01-05-AC-01: status=PASSED; due_now=true; gate=WO-CAP-01-05 completion; reason=WO-CAP-01-01 through WO-CAP-01-04 are DONE and no expired CAP-01 prerequisite remains.
- WO-CAP-01-05-AC-02: status=PASSED; due_now=true; gate=WO-CAP-01-05 completion; reason=Candidate e522266 and its tree-equivalent protected merge e348ee5 passed the complete automated, package, staging/recovery, and reporting matrix in run 37192774502.
- WO-CAP-01-05-AC-03: status=PASSED; due_now=true; gate=WO-CAP-01-05 completion; reason=The exact local-staging candidate and deterministic fixtures were exercised; five cases have normal passed final runs and the sixth used the accepted direct defect-retest path with all linked defects CLOSED/FIXED.
- WO-CAP-01-05-AC-04: status=PASSED; due_now=true; gate=WO-CAP-01-05 completion; reason=The product owner reviewed the code and evidence, confirmed successful direct retests, accepted the documented platform exception, and accepted CAP-01 on 2026-10-04 without granting production approval.

## Acceptance examples and test oracles

- **Positive oracle:** The full required matrix and manual package pass on the exact candidate digests deployed to the named staging environment, followed by explicit human acceptance.
- **Negative oracle:** A changed digest, missing/stale/skipped mandatory result, failed recovery, absent receipt, or missing human decision blocks capability acceptance.
- **Boundary oracle:** Acceptance covers the declared minimum and maximum supported configuration plus timeout, retry, concurrency, recovery, and compatibility edges applicable to the capability.
- **Evidence binding:** every executed result identifies specification revision 0.8, suite/input fingerprints, commit or candidate, environment, attempt, and evidence reference.

## Expectation sources and independent review

- Sources: confirmed product decisions, the linked capability, requirements REQ-001, REQ-002, REQ-016, REQ-017, process PRC-01, and cited architecture/security/design contracts.
- Positive expectation: The full required matrix and manual package pass on the exact candidate digests deployed to the named staging environment, followed by explicit human acceptance.
- Counterexample: A changed digest, missing/stale/skipped mandatory result, failed recovery, absent receipt, or missing human decision blocks capability acceptance.
- The planning derivation and human confirmation are recorded in ../../planning/13-cap01-readiness-review.md; candidate-bound implementation review remains mandatory before capability acceptance.

Candidate-bound code review and final human acceptance are recorded in
[the CAP-01 acceptance record](../../testing/manual/PRC-01/acceptance-record.md).

## Required tests

- TST-WO-CAP-01-05: gate completeness, candidate/digest equality, evidence freshness, and receipt validation.
- Full capability CI and BDD matrix on the unchanged candidate; no selective reuse substitutes for this final run.
- Every published `MT-*` case for PRC-01 executed on staging with atomic step results.
- Recovery and rollback/roll-forward drill appropriate to the capability's state and external effects.

Execution procedure: [CAP-01 manual acceptance execution guide](../../testing/manual/PRC-01/execution-guide.md).

## BDD and manual tests

BDD-AUTH-001 and BDD-PROJ-001 passed in protected CI. The published `MTP-PRC-01` package was executed on local staging. Five cases have normal passed run records; the sixth used Softwaretest.it's direct defect-retest path. All three resulting defects are CLOSED/FIXED, and the product owner explicitly accepted that evidence path despite the unused repeat run remaining `NOT_STARTED`.

## Softwaretest.it and CI reporting

Definitions must be idempotently published and field-level round-tripped before execution. All CI stage and individual results are reported with candidate identity and all statuses. A reporting-only failure retries the reporting stage and never reruns successful tests.

## CI retry and evidence reuse

Retry only a failed/aborted/invalid stage for an unchanged candidate. After a repair commit, rerun that stage plus stages invalidated by recorded change impact. Before capability acceptance, run the complete required matrix once against the exact unchanged candidate.

## Deployment and staging evidence

This workorder owns and closes the capability staging gate. Candidate `e522266`, local run `cap01-retest-e522266-01`, the tree-equivalent protected merge `e348ee5`, CI run `37192774502`, Softwaretest.it execution/defect identifiers, and the human decision are reconciled in the acceptance record.

## Documentation and evidence

- Updated contracts/ADRs only where their approved delta requires it
- Test definitions/results, architecture/security evidence, and redacted diagnostics
- Candidate commit/digests, configuration and identity scope, timestamps, attempts, and findings
- No invented pass, approval, cost, duration, or external receipt
- Final acceptance record: ../../testing/manual/PRC-01/acceptance-record.md

## Definition of Done

- All prerequisite workorders are DONE with current evidence
- Full matrix and required manual cases pass on the exact staged candidate
- Reporting receipts, recovery evidence, and independent implementation review are complete
- Authorised human capability acceptance is recorded; production remains separately unapproved

## Workorder completion versus capability acceptance

DONE proves this integrated acceptance result. CAP-01 is human-accepted for the recorded candidate and environment. Release promotion and production approval remain separate and ungranted.

## Events, rework, and cost

Record available intake, READY, start, wait/resume, review, acceptance, reopen, rework, intervention, escaped-defect, and cost evidence. Unknown time or cost remains unknown; no new dashboard is a prerequisite.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-00
- Required workorders: WO-CAP-01-01, WO-CAP-01-02, WO-CAP-01-03, WO-CAP-01-04
- Downstream acceptance owner: none; this is the capability acceptance workorder
- Numbering is an identifier, not permission to bypass this dependency graph. Test-definition publication may therefore complete before a lower-numbered implementation workorder.
- A changed prerequisite contract, ADR, design revision, test package, or candidate triggers documented impact analysis and may return this workorder to DRAFT/BLOCKED.
