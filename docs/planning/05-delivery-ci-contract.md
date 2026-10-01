# Delivery and CI Contract

Version: 0.1-draft
Status: DRAFT

## 1. Delivery principles

- Build once, identify by digest, and promote the unchanged candidate.
- No branch automatically deploys to any environment.
- Every promotion is a pull request with required evidence and human approval.
- Local staging is a real isolated Docker Compose profile, not a development server.
- Product code cannot begin before CAP-00 proves the delivery path and Softwaretest.it publishing readiness.
- Every capability ends with a local staging acceptance workorder.
- A production environment is not yet defined.

## 2. Branch model

Feature branches:
- Created from the intended integration base.
- Contain one bounded workorder outcome.
- Submit a pull request into test.

test:
- Integration branch for completed workorders.
- Requires scope, quality, architecture, security, and test checks.
- Never deploys automatically.

staging:
- Candidate branch.
- Accepts promotion from test only.
- Produces or selects the immutable release candidate.
- An operator manually deploys the candidate digest to local staging.
- Capability or release acceptance evidence is bound to this digest.

main:
- Accepted public baseline.
- Accepts promotion from staging only.
- No automatic deployment follows.
- A main merge is not production approval.

Direct pushes to test, staging, and main are prohibited.

## 3. Environments

Local development:
- Fast feedback and component services
- May use mocks and developer data
- Not acceptance evidence

CI:
- Reproducible checks and immutable result artefacts
- No interactive secrets
- Untrusted pull requests isolated from protected credentials

Local staging:
- Separate Compose project, networks, volumes, ports, credentials, and synthetic fixtures
- Starts from clean or explicitly versioned state
- Receives exact candidate digest
- Supports health, smoke, manual, recovery, and evidence collection

Production:
- DEFERRED
- Requires a separate environment, operator, backup, TLS, DNS, access, monitoring, RPO, RTO, rollout, and rollback contract

## 4. Artefact model

Each candidate contains:

- Immutable web, API, and worker container image digests
- Versioned database migration set
- Canonical API and workflow schemas
- Dependency lockfiles
- SBOM
- Build provenance or equivalent signed build metadata where implemented
- Test-definition version
- Architecture and security rule-set versions
- Evidence bundle references

Tags are convenience labels and are never the acceptance identity.

## 5. CI stage catalogue

CI-TS-01 — Contract consistency
- Trigger: every pull request
- Scope: planning and workorder indexes, schemas, stable IDs, references
- Oracle: no schema, reference, or transition violation; empty scope fails

CI-TS-02 — Formatting and static analysis
- Trigger: affected language or configuration
- Scope: TypeScript, Python, YAML, JSON, Markdown, Docker and infrastructure files
- Oracle: no blocking configured violation

CI-TS-03 — Architecture rules
- Trigger: source, package, build, or ARCH-rule changes
- Scope: dependency directions, cycles, module APIs, type leaks, composition roots
- Oracle: zero unauthorised dependencies; allowed fixture passes and forbidden fixture fails
- Implemented commands: locked Python architecture pytest suite, Import Linter contracts, and the pnpm TypeScript architecture suite
- Fail-closed controls: source discovery must be non-empty; retained positive fixtures pass; retained negative fixtures fail for the intended rule
- Current CI jobs: `Architecture / Python` and `Architecture / TypeScript`, each with a ten-minute timeout and read-only repository permission

CI-TS-04 — Unit tests
- Trigger: affected modules
- Scope: domain, application, parsers, validation, policies, state machines
- Oracle: all required tests pass; no mandatory suite has zero discovered tests

CI-TS-05 — Component tests
- Trigger: affected service or adapter
- Scope: API, worker, web components, persistence adapters, provider adapters
- Oracle: declared component contracts pass against controlled dependencies

CI-TS-06 — Schema and consumer contracts
- Trigger: API, workflow, event, connector, callback, or persistence contract changes
- Scope: OpenAPI, JSON Schema, compatibility, round-trip
- Oracle: compatible changes or explicit approved version break
- Softwaretest.it definition publication: feature branches validate a lossless local CAP-01 manifest and adapter behavior; trusted `test`, `staging`, and `main` pushes use the protected environment to publish the six committed manual definitions idempotently and require field- and ordered-step read-back before the job can pass. Publication creates no execution result.

CI-TS-07 — Integration tests
- Trigger: data, adapter, execution, or infrastructure changes
- Scope: PostgreSQL, Qdrant, Apistra runtime persistence and dispatch, model and connector simulators
- Oracle: state, idempotency, transactions, and error paths match the contract

CI-TS-08 — Automated BDD end-to-end
- Trigger: business behaviour and final candidate gate
- Scope: published workflow journeys with stable BDD IDs
- Oracle: externally observable behaviour matches the approved specification

CI-TS-09 — Security tests
- Trigger: every candidate; deeper authenticated tests for affected attack surfaces
- Scope: authorisation, project isolation, SSRF, injection, secrets, sessions, keys, policy, egress
- Oracle: required positive controls succeed and negative controls fail without data or side effects

CI-TS-10 — Supply-chain checks
- Trigger: every candidate and dependency change
- Scope: secrets, dependencies, licences, container, SBOM, workflow and deployment configuration
- Oracle: no unhandled blocking finding; missing or empty report fails

CI-TS-11 — Migration tests
- Trigger: database, schema, persistence, or version changes
- Scope: upgrade from supported previous state, failed migration recovery, forward compatibility
- Oracle: deterministic success or safe documented recovery

CI-TS-12 — Deterministic resource, boundary-load, and workload limits
- Trigger: resource declarations, input/batch limits, budget policies, runtime configuration, or release candidates
- Scope: declared CPU, memory, PID, temporary-storage and loopback-exposure limits plus deterministic input, batch, retry, token, and cost bounds as those contracts are introduced; source-code complexity is owned separately by CI-TS-17
- Oracle: every applicable bound is explicit, fail-closed, and exercised at/below/above its boundary; an empty applicable suite fails
- Current command: `uv run --project backend pytest --no-cov backend/tests/resource`; the separate aggregate backend run enforces the repository-wide coverage threshold.
- Explicit limitation: pipeline load coverage is restricted to deterministic at/below/above boundary cases, bounded batches, declared container resources, and fail-closed overload behavior that do not require a running installation or shared-runner timing. It does not measure latency, throughput, or concurrent load and does not claim sustained-load, scalability, or capacity evidence. There is currently no running representative candidate with controlled hardware, data scale, warm-up, and measurement windows from which a defensible performance threshold could be derived.
- Activation rule for future performance gates: add a separately identified stage only after a representative running candidate and reproducible environment exist; record workload, hardware, data scale, warm-up, duration, thresholds, variance, and abort limits before execution.

CI-TS-13 — Resilience and recovery
- Trigger: durable runtime, data, deployment, and final candidate
- Scope: process restart, worker loss, endpoint timeout, uncertain response, restore, rollback or roll-forward
- Oracle: no duplicate unsafe side effect and no unaudited state loss

CI-TS-14 — UI accessibility and visual checks
- Trigger: UI or design-token changes
- Scope: approved pages, states, viewports, keyboard, focus, automated accessibility
- Oracle: no blocking deviation from approved reference or WCAG contract

CI-TS-15 — Packaging and Compose smoke
- Trigger: every candidate
- Scope: clean build, configuration, migration, startup, readiness, liveness, offline profile
- Oracle: exact image digest starts and passes smoke checks

CI-TS-16 — Softwaretest.it reporting
- Trigger: after all other stages, and independently for retry
- Scope: all actual results including passed, failed, skipped, error, and cancelled
- Oracle: idempotent upload and round-trip receipt count and status match the immutable result bundle

CI-TS-17 — Cyclomatic complexity
- Trigger: every Python, TypeScript, TSX, JavaScript, lint-configuration, or CI change
- Scope: all Python product, engineering, and repository-tool functions plus all TypeScript/TSX web and JavaScript repository-tool functions
- Metric and tools: classic McCabe cyclomatic complexity, measured by Ruff `C901` for Python and ESLint `complexity` for TypeScript/TSX/JavaScript
- Oracle: every function has complexity at most 10; there are no per-file suppressions, grandfathered violations, or higher subsystem limits
- Fail-closed controls: the complete configured source scope must pass; retained positive Python and TypeScript fixtures must pass; retained functions with complexity 11 must be rejected by their respective analyser
- Current CI job: `Contract and static checks`, with the pinned Ruff, ESLint, TypeScript parser, and repository lockfiles

CI-TS-18 — Python code conventions
- Trigger: every Python, Python-tooling, dependency-lock, convention-document, or CI change
- Scope: Python product code plus repository-owned engineering and release tools; tests retain readable scenario literals but remain subject to Ruff and formatting
- Tools: Ruff for the common rule set and annotations, mypy in strict mode for product code, and the pinned wemake-python-styleguide checks `WPS226` and `WPS432` for repeated strings and magic numbers
- Oracle: all applicable source passes without blanket suppressions; public and internal product functions are fully typed; repeated domain/protocol strings and non-trivial numeric policy values are named constants
- Fail-closed controls: a retained conforming fixture passes, retained overused-string and magic-number fixtures fail with their exact expected rule identifiers, and an explicit scan rejects blanket `noqa`, `type: ignore`, Ruff, or Pylint disable-all directives
- Current CI job: `Contract and static checks`, using only dependencies pinned in `backend/uv.lock`

Pipeline mapping rule:
- Each executable stage has its own named workflow step or job and an explicit command. A combined test command must not be presented as evidence for stages for which it discovered no applicable tests.
- Focused Python stage commands disable the global coverage plugin because a single slice cannot cover the complete backend. A subsequent aggregate `pytest backend/tests` run is the only repository-wide coverage oracle and remains blocking.
- Candidate packaging depends on contract/static, architecture, test, and security jobs. It cannot create a green result bundle while a prerequisite quality job is failed or incomplete.

## 6. Stage execution and retries

For the same candidate:

- Retry only failed, cancelled, or technically invalid stages.
- Reuse successful independent stages when suite, inputs, configuration, and relevant candidate parts have matching fingerprints.
- Record every attempt.
- A Softwaretest.it-only failure retries CI-TS-16 without rerunning tests.

After a repair commit:

- Rerun the failed stage.
- Rerun stages invalidated by the changed code, contracts, dependencies, configuration, migrations, test definitions, policies, or environment.
- When impact is unclear, widen the stage set and record the reason.

Before a staging acceptance:

- Run the complete scope-required matrix once against the exact unchanged candidate.

## 7. CAP-00 bootstrap gate

CAP-00 contains no business behaviour. It must prove:

- protected branch and review flow
- reproducible monorepo build
- minimal web, API, and worker skeleton
- immutable images and candidate manifest
- Docker Compose local staging profile
- externalised configuration and protected secrets
- real or no-op migration mechanism
- readiness, liveness, and smoke checks
- structured logging, basic metrics, correlation, and deployment marker
- SBOM and baseline supply-chain checks
- automated result artefacts
- Softwaretest.it preflight, publishing manifest, example result upload, round-trip, or an explicit blocking finding without invented endpoints
- manual deployment of the exact digest to local staging
- tested rollback or roll-forward recovery
- retained evidence with commit, digest, stage attempts, environment, and recovery result

No business workorder becomes READY until CAP-00 and publishing readiness pass.

## 8. Softwaretest.it delivery contract

Before a write:

1. Retrieve the authoritative OpenAPI document from the intended instance.
2. Verify base URL, version, authentication, scopes, rate limits, resources, statuses, steps, evidence, and idempotency.
3. Run a read-only preflight.
4. Validate synthetic example requests locally.
5. Use minimum project-scoped credentials.

Required logical resources:

- Apistra project
- Versioned release or capability test plan
- Capabilities and processes
- Automated and manual test definitions
- Ordered manual steps
- Test runs, attempts, statuses, evidence, and defects

If the API lacks a required capability, publishing remains BLOCKED and a lossless local manifest is retained. No approximate endpoint or flattened manual test is allowed.

## 9. Capability staging gate

A capability is accepted only when:

- all workorders are DONE;
- the complete required matrix passed on the unchanged candidate;
- all CI results are confirmed in Softwaretest.it;
- the operator deployed the exact digest to isolated local staging;
- migrations and configuration completed;
- capability smoke, acceptance, security, and UI tests passed;
- synthetic users and fixtures were verified;
- required manual tests were executed from Softwaretest.it;
- logs, metrics, traces, and audit show expected behaviour;
- recovery is understood and, for elevated risk, demonstrated;
- a human accepted the capability.

## 10. Recovery

CAP-00 selects and proves either:

- rollback to the previous compatible image and schema state; or
- roll-forward to a corrected candidate when database compatibility prevents rollback.

Backups and restore are distinct evidence. A backup without a successful restore test is not recovery proof.

## 11. Production boundary

No production environment, deployment identity, or automatic release exists. Promotion to main records an accepted source and candidate baseline only. Any future production work requires explicit authorisation and a separate approved contract.
