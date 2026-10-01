# Apistra Test Concept

Version: 0.1-draft
Status: DRAFT
Assurance profile: EXTENDED

## 1. Control summary

**Result:** This concept defines how Apistra plans, designs, prepares, executes, evaluates, reports, and closes testing across workorders, capabilities, releases, and environments.

**Relationship to the test architecture:** The system-centred test architecture defines what must be tested and how risks map to system structures and processes. This test concept defines who performs which testing activities, when they occur, which gates apply, and what evidence is required.

**Current position:** CAP-00 automated suites, candidate verification, staging/recovery, human acceptance, and authenticated Softwaretest.it reporting are hosted-verified. Business-capability tests, their definition publication, complete manual process execution, and browser/screen-reader measurement remain pending.

**Next responsible step:** Complete CAP-00 external acceptance, then apply this concept to CAP-01 expectation review and test-definition workorders before implementation READY.

## 2. Purpose, scope, and non-goals

The test process provides objective evidence that a bounded Apistra change satisfies its approved product, architecture, security, delivery, design, and workorder contracts without invalidating accepted behavior.

In scope:

- planning and independent review of expectations;
- static, unit, component, contract, integration, architecture, security, end-to-end, manual, accessibility, performance, resilience, migration, packaging, and recovery testing;
- synthetic test data and service virtualisation;
- CI execution, selective retry, staging acceptance, evidence retention, defect/retest handling, and Softwaretest.it reporting;
- workorder, capability, release, and future production test gates.

Non-goals:

- using coverage percentage as a substitute for behavioral adequacy;
- treating a green scanner, build, index validator, or AI evaluation as sole acceptance authority;
- destructive or unauthorised testing of external systems;
- testing production before a production test and environment contract exists;
- duplicating system models, CI-stage definitions, or manual-step formats already governed by their canonical contracts.

## 3. Binding test basis and precedence

Tests derive their expectations from approved sources in this order:

1. confirmed product decisions and requirement/capability contracts;
2. approved architecture, security, delivery, design, API, schema, and external-service contracts;
3. independently reviewed workorder expectations with examples and counterexamples;
4. observed current behavior only where an approved compatibility contract preserves it.

Implementation code and tests are evidence about behavior, not independent authority for the expected result. A contradiction stops the affected workorder until the authoritative expectation is resolved.

Canonical references:

- `docs/planning/01-product-scope.md`
- `docs/planning/03-architecture.md`
- `docs/planning/04-security-concept.md`
- `docs/planning/05-delivery-ci-contract.md`
- `docs/planning/06-test-architecture.md`
- `docs/planning/07-design-contract.md`
- `docs/capabilities/` and `docs/workorders/`
- `docs/architecture/testing.md`

## 4. Quality objectives and risk policy

Test intensity follows probability, impact, detectability, reversibility, exposure, and uncertainty. It does not follow file count or implementation effort.

Highest-priority risks include:

- cross-project disclosure or mutation;
- secret disclosure;
- unauthorised writes or approvals;
- unrestricted egress, SSRF, or prompt-driven tool abuse;
- duplicate external effects and unsafe retries;
- loss or corruption of durable run state;
- mutable published definitions;
- stale knowledge after source deletion;
- Process API idempotency failures;
- failed migration, backup, restore, rollback, or roll-forward.

Every planned test identifies the risk, requirement, process or structure, test oracle, execution stage, data/identity scope, and required evidence. Unknown risk or an untestable critical rule blocks READY.

## 5. Test organisation and responsibilities

Product owner:

- confirms critical product behavior and accepts or rejects capability outcomes;
- decides explicit product deviations, but cannot waive unreviewed security findings alone.

Workorder implementer:

- implements the bounded result and its assigned automated tests;
- records change impact, evidence, and known limitations;
- does not perform the independent implementation acceptance review.

Independent reviewer:

- derives expectations separately for STANDARD and EXTENDED work;
- reviews implementation and tests against the approved revision;
- records discrepancies, residual risks, and invalidated evidence.

Test designer or QA role:

- derives test conditions, cases, data, oracles, coverage, and traceability;
- preserves independence between BDD automation and manual process cases.

Security reviewer:

- reviews affected SEC rules, safe test authority, identities, environment configuration, findings, and retests.

Operator or maintainer:

- deploys the exact candidate manually to staging;
- verifies environment identity, health, diagnostics, recovery, and cleanup.

Authorised manual tester:

- executes published manual cases on the named staging candidate;
- records each step result, evidence, defects, and retests without exposing secrets.

Release approver:

- evaluates the complete due evidence and provides the separate release decision;
- does not infer production approval from a merge or capability acceptance.

One person may hold multiple roles only where independence and separation-of-duty requirements remain satisfied and documented.

## 6. Test planning by delivery level

### 6.1 Workorder

Before READY, identify affected risks, contracts, architecture/security rules, exact test groups, later capability tests, environments, data, and evidence. Before DONE, every test assigned to the workorder has passed or received an authorised explicit disposition, and the EXTENDED implementation review is complete.

### 6.2 Capability

The final capability workorder executes the complete scope-required matrix once against the unchanged candidate, publishes all results, deploys that candidate to isolated staging, executes required manual process/UI/security cases, verifies observability and recovery, and obtains human acceptance.

### 6.3 Release

The release gate repeats cross-capability regression for the included scope, confirms no blocking architecture/security finding, verifies legal/documentation obligations, and binds the decision to the exact candidate. A release is not production deployment.

### 6.4 Production

Production testing is NOT DEFINED. It requires an approved environment, data, access, safety, load, recovery, monitoring, and rollback contract plus explicit human authorisation.

## 7. Test levels and ownership

- Static and contract consistency: repository structure, schemas, IDs, links, formatting, types, and lint rules.
- Architecture: dependency directions, cycles, public module boundaries, composition roots, non-empty scope, and retained allowed/forbidden fixtures.
- Unit: domain invariants, policies, parsing, validation, state transitions, limits, redaction, and error taxonomy.
- Component: application services and UI components against controlled ports, fakes, or simulators.
- Contract: OpenAPI, JSON Schema, workflow, event, connector, callback, provider, and engineering-adapter compatibility.
- Integration: PostgreSQL, Qdrant, durable execution, migrations, outbox/inbox, and controlled external simulators.
- Automated BDD E2E: stable, externally observable critical journeys expressed as Given/When/Then.
- Manual process and UI/UX: independent atomic cases covering complete user journeys, states, roles, errors, accessibility, and recovery.
- Security and privacy: actual enforcement points with valid positive and negative identity/project controls.
- Performance and resource: representative synthetic profiles, budgets, concurrency, rate, duration, token, and cost limits.
- Resilience and recovery: restart, worker loss, timeout, cancellation, uncertain response, backup restore, rollback, and roll-forward.
- Packaging and staging: clean build, immutable images, manifest, SBOM, migration, health, smoke, offline profile, and exact-candidate recovery.

The CI-stage identifiers CI-TS-01 through CI-TS-16 and their canonical scopes remain defined in `docs/planning/05-delivery-ci-contract.md`.

## 8. Test design techniques

Use the techniques that expose the named risk:

- equivalence partitioning and boundary-value analysis for schemas, limits, timeouts, and budgets;
- decision tables for policies, roles, citation behavior, approval, and release gates;
- state-transition testing for drafts, publication, runs, attempts, human tasks, synchronisation, callbacks, licences, and triggers;
- pairwise or risk-selected combinations for provider, connector, locale, policy, and configuration variants;
- property-based tests for parsers, canonical serialisation, idempotency, invariants, and redaction;
- metamorphic checks for non-deterministic AI behavior where exact output is not a valid oracle;
- contract and compatibility fixtures for versioned interfaces;
- fault injection for retries, partial failure, uncertain external responses, restart, and recovery;
- abuse and misuse cases for identity, project isolation, secrets, egress, tools, and prompt injection;
- exploratory charters for emerging behavior, always in addition to mandatory scripted cases.

Each test has an explicit expected result. Probabilistic output uses deterministic structural/property oracles and calibrated evaluation evidence; it never passes solely because an LLM judge says so.

## 9. Test case identification and traceability

- CI stages: `CI-TS-NN`
- Architecture tests: `AT-ARCH-NNN`
- Automated BDD scenarios: stable domain-oriented `BDD-*` IDs
- Manual test cases: stable `MT-*` IDs grouped into `MTP-PRC-NN` process packages
- Workorder-focused groups: `TST-WO-CAP-NN-NN`
- Defects: stable external Softwaretest.it ID when available; lossless local ID until round-trip is confirmed

Every test maps requirement → capability → process/structure → workorder → risk → environment/data → candidate → result/evidence. BDD and manual IDs remain independent unless they genuinely cover the same externally observable behavior.

## 10. Test environments

Local development:

- fastest feedback with controlled data and optional fakes;
- useful for implementation evidence, never capability acceptance.

CI:

- clean, reproducible, non-interactive, and least-privileged;
- untrusted pull requests receive no deployment, registry-write, reporting-write, or signing secrets.

Isolated local staging:

- separate Compose project, networks, volumes, ports, identities, configuration, and synthetic data;
- manually receives the exact candidate digest;
- is the current capability acceptance environment.

External test services:

- require explicit authorisation, minimal project-scoped credentials, rate/cost limits, and cleanup;
- are replaced by deterministic simulators where the real service is unsafe, unavailable, costly, or non-repeatable.

Production:

- excluded until GATE-PROD and a production test contract exist.

## 11. Test data, identities, and fixtures

- Use synthetic, deterministic, versioned data by default.
- Allocate unique project, identity, run, source, workflow, and test-run identifiers per execution.
- Generate fixtures idempotently and verify them before test execution.
- Keep setup, verification, reset, and cleanup explicit and independently reportable.
- Use distinct own-project, foreign-project, anonymous, invalid, expired, revoked, and under-scoped principals where relevant.
- Resolve passwords/tokens through protected runtime references; never persist them in cases, logs, screenshots, exports, or evidence.
- Do not copy production or third-party data into test environments without a separately approved privacy process.
- Preserve deterministic model/embedding, connector, callback, tool, and clock simulators for normal and failure behavior.

## 12. Entry criteria

A test activity may start only when:

- the exact specification/workorder revision and candidate or source commit are identified;
- expected behavior, examples, counterexamples, and oracle are approved at the required assurance level;
- required contracts, ADRs, ARCH/SEC rules, and design references are available;
- the target environment and identities are authorised and known;
- fixtures, service virtualisation, configuration, and safe limits are ready;
- required tooling and test definitions are versioned;
- active blocking defects do not make the result meaningless;
- rollback, cleanup, or safe abort is defined for state-changing tests.

If an entry criterion is absent, record `BLOCKED` or `NOT EXECUTED`; do not translate missing evidence into PASSED.

## 13. Exit and gate criteria

Workorder exit requires:

- all workorder-assigned tests executed with accepted results;
- no unhandled blocking defect or expired/unapproved exception;
- applicable ARCH/SEC evidence and independent implementation review complete;
- documentation, traceability, result bundle, and Softwaretest.it reporting complete.

Capability exit additionally requires:

- every constituent workorder DONE;
- the full scope matrix passed once on the unchanged candidate;
- exact candidate staged manually with migration, health, smoke, observability, and recovery evidence;
- all required manual process, permission, security, UI/UX, and accessibility tests executed;
- authorised human capability acceptance.

No average pass percentage can override a failed or missing mandatory criterion.

## 14. Test execution states

Use these result meanings consistently:

- `PASSED`: the stated oracle was observed for the identified attempt.
- `FAILED`: behavior contradicted the oracle.
- `SKIPPED`: execution was deliberately omitted under an explicit rule; no pass is implied.
- `ERROR`: infrastructure, setup, tooling, or execution failure prevented a valid verdict.
- `CANCELLED`: the attempt was stopped before a valid verdict.

`BLOCKED`, `NOT EXECUTED`, `UNKNOWN`, `STALE`, and `CONTRADICTORY` are planning/evidence descriptions, not invented Softwaretest.it result payloads. Map only to fields verified in the active OpenAPI contract.

## 15. Defect and deviation management

Severity:

- S1 Critical: confidentiality/integrity breach, unauthorised external effect, unrecoverable data loss, or unusable installation. Blocks every affected gate.
- S2 Major: critical journey or mandatory control fails without a safe viable workaround. Blocks the affected workorder/capability/release.
- S3 Moderate: bounded functional or quality failure with a safe documented workaround. Blocks its acceptance criterion unless explicitly dispositioned by the responsible gate owner.
- S4 Minor: cosmetic, wording, or low-impact documentation defect with no control failure. May be deferred with traceable ownership.

Lifecycle: observed → triaged → assigned → fixed or explicitly dispositioned → ready for retest → retested → closed. Rejection, duplicate, deferred, and accepted-deviation outcomes retain reason, authority, scope, expiry/review trigger, and original evidence.

A security provider limitation follows the security contract and never turns the failed or unsupported individual control into PASSED.

## 16. Automation and CI strategy

- Prefer deterministic tests at the lowest level that can prove the behavior, then retain critical journey coverage at higher levels.
- A test suite must fail if discovery is unexpectedly empty.
- Architecture/security validators retain positive and negative control fixtures.
- Flaky tests are defects. Quarantine requires owner, reason, risk, expiry, replacement gate, and visible non-pass status.
- Parallel execution is allowed only with isolated data, identities, ports, volumes, and rate/cost budgets.
- Every stage emits machine-readable results even on failure, error, skip, or cancellation.
- Artifact upload may be best-effort only when lossless primary evidence remains available; substantive gates stay blocking.

Selective retry:

- unchanged candidate: retry only failed, cancelled, or technically invalid stages;
- repair commit: rerun the failed stage and stages invalidated by documented change impact;
- reporting-only failure: retry only reporting/outbox delivery;
- capability/release gate: run the full required matrix once on the exact unchanged candidate.

## 17. Non-functional testing

Security/privacy:

- test actual enforcement with authorised principals, project ownership, effective rights, policy/configuration version, and safe negative controls;
- retain findings and retest evidence in protected storage.

Performance/resources:

- define workload, data scale, concurrency, warm-up, measurement window, hardware/environment, thresholds, and abort limits before execution;
- do not invent representative thresholds before representative runtime behavior exists.

Resilience/recovery:

- inject service loss, worker interruption, timeout, duplicate delivery, uncertain response, corrupted/failed migration where safely simulated, and restore scenarios;
- prove absence of duplicate unsafe effects and unaudited state loss.

Accessibility/UI:

- test approved viewports and states, keyboard order, focus, labels, semantics, reduced motion, contrast, zoom, screen-reader output, error wording/association, and preserved user input;
- automated accessibility checks complement, not replace, manual evaluation.

Compatibility/versioning:

- verify supported upgrade paths, schema/API compatibility, stored snapshot readability, import/export version behavior, and explicit unknown-version rejection.

Offline operation:

- an offline-configured candidate must complete its local journey without hidden external communication.

## 18. Manual and exploratory testing

Every business process has an independent manual process package. Each case starts from a logged-out staging session at the sign-in page, uses verified synthetic users/data, resolves login and navigation into atomic role-prefixed steps, and records exactly one action or observation with matching data and result per step.

Exploratory sessions have a charter, scope, risk, time box, environment, tester, notes, findings, and evidence. They never replace mandatory scripted process, permission, security, UI/UX, accessibility, or recovery cases.

## 19. Softwaretest.it test management

- Verify the authoritative OpenAPI contract before every new class of write.
- Use minimum project-scoped credentials and never place tokens or passwords in definitions or evidence.
- Publish requirements, capabilities, processes, BDD scenarios, manual cases, ordered steps, and CI mappings idempotently.
- Read back fields and step order; creation success alone is insufficient.
- Report every CI result/status and bind it to commit, candidate, suite, stage, test, attempt, environment, and evidence.
- Preserve a lossless local outbox when publishing is unavailable.
- A reporting failure blocks acceptance but does not invalidate a valid completed test attempt.

## 20. Evidence and reporting

Every valid execution record includes:

- specification, rule, test-definition, and tool/configuration versions;
- commit, candidate and image digests, environment, deployment revision, data/fixture version, and relevant identities/policies;
- test/stage/attempt identifiers, timestamps, result state, expected and actual safe summary;
- logs, metrics, traces, screenshots, reports, or audit references as required;
- defects, deviations, retests, review, Softwaretest.it receipt, and human acceptance where applicable.

Evidence is immutable, classified, redacted, retention-bound, and access-controlled. A hash proves identity, not correctness.

## 21. Metrics and reporting boundaries

Use available evidence to track execution counts by result, requirement/risk coverage, defect severity and escape, flaky/quarantine age, stage duration, rework, review wait, and candidate lead time. Unknown values remain unknown.

Do not use code coverage, test count, pass percentage, velocity, or AI-judge score as a standalone quality or productivity claim. Coverage thresholds are regression controls; risk and oracle adequacy require review.

## 22. Testware versioning and change impact

- Test definitions, fixtures, simulators, baselines, schemas, policies, and evidence formats are versioned with the repository.
- Stable test IDs survive wording or implementation changes; semantic expectation changes create a new content revision and invalidate affected approvals/evidence.
- Deleted tests remain historically traceable and require an explicit replacement or not-applicable decision.
- Candidate evidence records test-suite and relevant-input fingerprints.
- Changes to product behavior, contracts, dependencies, migrations, policies, identity/project boundaries, environment, or tests trigger transitive impact analysis.
- Product and artifact versioning follows `VERSIONING.md`; test evidence remains bound primarily to immutable commit/candidate identity.

## 23. Current CAP-00 application

Implemented and hosted-verified:

- repository/contract checks, static analysis, architecture rules and negative fixtures;
- Python and web tests with configured coverage thresholds;
- health/component, schema, fixture, secret-scan, dependency-audit, packaging, Compose staging, marker, controlled failure, and recovery checks;
- public Softwaretest.it OpenAPI preflight, adapter tests, result bundle, and dry-run outbox.

Still pending for CAP-00 acceptance:

- live protected-branch configuration;
- authenticated Softwaretest.it project/test-plan write and field-level read-back;
- independent implementation review;
- manual CAP00-MAN-001 execution and human bootstrap acceptance.

## 24. Review and maintenance

This concept is reviewed when a new capability introduces a new actor, environment, identity boundary, data class, external service, test type, result state, release path, or material quality risk. Changes receive a changelog entry and independent review appropriate to their assurance profile.

The document remains DRAFT until product, architecture, security, QA, and delivery responsibilities confirm the version 0.1 test process. Approval of this document does not approve a capability or production release.
