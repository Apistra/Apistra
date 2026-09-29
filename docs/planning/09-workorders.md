# Workorder Catalogue

Version: 0.3-draft
Status: DRAFT

All workorders use EXTENDED assurance unless a later reviewed delta justifies a lower profile. Every workorder requires approved expectations, implementation evidence, and the specified gate. CAP-00 implementation is ready for independent and external acceptance, but CAP-00 is not DONE.

## Common stop conditions

Stop and report when:

- the observed repository contradicts the workorder;
- a product, architecture, security, or design decision is missing;
- work would exceed the named capability;
- required test or Softwaretest.it contracts are unavailable;
- the candidate, local staging environment, or authorised test scope is unavailable;
- a blocking finding exists;
- a workorder would introduce automatic deployment;
- a business workorder is attempted before CAP-00 passes.

## CAP-00 workorders

### WO-CAP-00-01 — Establish repository governance and planning checks

Status: IMPLEMENTED — live branch protection remains blocked pending repository-administrator authorisation

Result:

Protected branch flow, planning document validation, pull-request templates, ownership, issue templates, and required-check definitions exist for feature to test to staging to main.

In scope:

- branch protection specification
- CODEOWNERS or equivalent ownership
- contribution policy stating that external contributions are not accepted yet
- security reporting policy
- licence placeholders pending legal text
- local contract validation

Acceptance:

- direct-push prohibition is configured or documented as blocked until repository administration is authorised;
- no workflow automatically deploys;
- protected configuration cannot be weakened by an ordinary feature pull request;
- CI-TS-01 executes with positive and negative fixtures.

Tests: CI-TS-01, CI-TS-02, CI-TS-10.

### WO-CAP-00-02 — Create the monorepo walking skeleton

Status: IMPLEMENTED AND HOSTED VERIFIED — independent review remains acceptance evidence

Result:

Minimal web, API, and worker processes build and expose non-business health behaviour through documented composition roots.

In scope:

- planned package boundaries
- pinned runtime and package-manager versions
- minimal health interfaces
- no business entities or workflow behaviour
- one installable Python backend package with module-first internal layers
- public-only cross-module contracts
- retained positive and negative architecture fixtures

Acceptance:

- clean clone builds reproducibly;
- services start without external SaaS;
- architecture tests prove ARCH-001, ARCH-010, ARCH-011, and ARCH-013;
- forbidden dependency fixture fails.

Implementation note: ADR-019 resolves the repository-layout decision. Web, API, and worker health processes, the complete local test matrix, and packaging path are implemented. GitHub Actions run 36618729112 verified the committed walking skeleton. This workorder is not DONE until the independent review is accepted.

Tests: CI-TS-02 through CI-TS-07, CI-TS-15.

### WO-CAP-00-03 — Package immutable container candidates

Status: IMPLEMENTED AND HOSTED VERIFIED — GitHub Actions run 36618729112 built the committed candidate, archives, manifest, checksums, and SPDX SBOM

Result:

Web, API, and worker images are built once, identified by digest, accompanied by candidate manifest and SBOM, and usable without source mounts.

Acceptance:

- image digest is stable for the produced artefact;
- runtime configuration and secrets are external;
- containers run with declared minimal rights;
- candidate manifest links commit, images, schemas, migrations, rule versions, and test definitions.

Tests: CI-TS-10, CI-TS-15.

### WO-CAP-00-04 — Establish isolated local staging and recovery

Status: IMPLEMENTED AND HOSTED VERIFIED — GitHub Actions run 36618729112 verified isolated staging, failure detection, and recovery with unchanged image IDs

Result:

An operator manually deploys the exact candidate to an isolated Compose staging profile and demonstrates health, diagnostics, and rollback or roll-forward.

Acceptance:

- separate project name, network, volumes, ports, and credentials;
- exact digest verified before and after deployment;
- no automatic branch deployment;
- deployment marker and correlated logs available;
- controlled failed deployment recovers to a healthy known state.

Tests: CI-TS-11, CI-TS-13, CI-TS-15; manual bootstrap smoke.

### WO-CAP-00-05 — Establish Softwaretest.it publishing readiness

Status: PARTIALLY IMPLEMENTED — public contract, client, outbox, redaction, status and idempotency tests pass; authenticated round-trip blocked pending authorised API access

Result:

The authoritative OpenAPI contract is verified and synthetic test definitions and results can be synchronised idempotently with field-by-field round-trip.

Acceptance:

- actual base URL, API version, authentication, scopes, resources, status semantics, and idempotency are recorded;
- project and versioned test-plan mapping are verified;
- ordered manual steps remain structured;
- all result statuses can be reported;
- reporting retry does not rerun tests;
- secrets are redacted;
- unsupported required API behaviour produces a lossless blocked manifest, not an invented request.

Tests: contract tests, CI-TS-16, negative duplicate and partial-failure cases.

### WO-CAP-00-06 — Provide synthetic staging fixtures

Status: IMPLEMENTED — descriptors are engineering-only and do not introduce CAP-01 authentication behavior

Result:

An idempotent fixture tool creates and verifies synthetic Administrator, project, data, protected credential references, test-run isolation, reset, and cleanup.

Acceptance:

- no production or foreign data is touched;
- repeated setup is deterministic;
- concurrent runs are isolated;
- secret values do not enter definitions or evidence.

Tests: CI-TS-07, CI-TS-09, fixture self-tests.

### WO-CAP-00-07 — Complete bootstrap candidate gate

Status: BLOCKED — branch protection, authorised Softwaretest.it round-trip, independent review, and human acceptance remain

Result:

The complete CAP-00 matrix passes, results are reported, the unchanged candidate is manually deployed to local staging, recovery is demonstrated, and a human accepts the bootstrap.

This is the only workorder that may close CAP-00.

## CAP-01 workorders

- WO-CAP-01-01 — Implement local Administrator bootstrap and revocable session
- WO-CAP-01-02 — Implement organisation installation and isolated project lifecycle
- WO-CAP-01-03 — Implement project-context enforcement and audit
- WO-CAP-01-04 — Publish and verify PRC-01 test definitions
- WO-CAP-01-05 — Accept CAP-01 on local staging

Key acceptance:

- local offline sign-in works;
- no second bootstrap Administrator can be created through race or replay;
- own-project actions succeed and foreign-project actions fail without disclosure;
- project lifecycle is audited;
- future identity adapters do not alter domain rules.

## CAP-02 workorders

- WO-CAP-02-01 — Implement encrypted project secret references
- WO-CAP-02-02 — Implement model and embedding endpoint catalogue
- WO-CAP-02-03 — Implement versioned agents and explicit fallback
- WO-CAP-02-04 — Implement governed tool contracts and approval classification
- WO-CAP-02-05 — Implement configurable limits and budget decisions
- WO-CAP-02-06 — Publish and verify CAP-02 test definitions
- WO-CAP-02-07 — Accept CAP-02 on local staging

Key acceptance:

- secrets never reappear;
- endpoints can be validated without logging credentials;
- agents retain endpoint and configuration versions;
- writes default to approval;
- limits warn and stop deterministically.

## CAP-03 workorders

- WO-CAP-03-01 — Define connector SDK, capability manifest, and compliance kit
- WO-CAP-03-02 — Implement file or directory connector
- WO-CAP-03-03 — Implement REST connector with SSRF protections
- WO-CAP-03-04 — Implement Git connector
- WO-CAP-03-05 — Implement manual, scheduled, and incremental synchronisation contract
- WO-CAP-03-06 — Publish and verify CAP-03 test definitions
- WO-CAP-03-07 — Accept CAP-03 on local staging

Key acceptance:

- connector output uses canonical documents and provenance;
- retries do not duplicate active records;
- errors identify connector, source item, attempt, and safe cause;
- outbound destinations obey the active network profile.

## CAP-04 workorders

- WO-CAP-04-01 — Implement canonical document and provenance model
- WO-CAP-04-02 — Implement extraction, cleaning, metadata, and chunking pipeline
- WO-CAP-04-03 — Implement versioned embedding configuration
- WO-CAP-04-04 — Implement Qdrant adapter behind vector-store port
- WO-CAP-04-05 — Implement cited retrieval
- WO-CAP-04-06 — Implement update, deletion, and reconciliation
- WO-CAP-04-07 — Publish and verify PRC-02 test definitions
- WO-CAP-04-08 — Accept CAP-04 on local staging

Key acceptance:

- every retrieved chunk maps to source, version, and location;
- removal deactivates all derived retrieval data;
- reconciliation detects orphaned or stale records;
- citations can be required by workflow policy.

## CAP-05 workorders

- WO-CAP-05-01 — Define canonical versioned workflow schema
- WO-CAP-05-02 — Implement graph and node validation
- WO-CAP-05-03 — Review, refine, and approve the produced visual design references
- WO-CAP-05-04 — Implement visual workflow editor
- WO-CAP-05-05 — Implement YAML and JSON editor with semantic round-trip
- WO-CAP-05-06 — Implement draft lifecycle and conflict handling
- WO-CAP-05-07 — Implement immutable publication
- WO-CAP-05-08 — Publish and verify PRC-03 test definitions
- WO-CAP-05-09 — Accept CAP-05 on local staging

Key acceptance:

- visual and canonical forms are semantically identical;
- invalid graphs identify actionable locations;
- publication creates a complete immutable snapshot;
- old versions remain runnable until disabled.

## CAP-06 workorders

- WO-CAP-06-01 — Select durable execution engine through approved ADR
- WO-CAP-06-02 — Implement run and node-attempt state machines
- WO-CAP-06-03 — Implement versioned Process API contracts
- WO-CAP-06-04 — Implement start idempotency and project API keys
- WO-CAP-06-05 — Implement durable node execution and checkpoints
- WO-CAP-06-06 — Implement status, result, cancellation, and safe errors
- WO-CAP-06-07 — Implement signed callbacks with retry
- WO-CAP-06-08 — Implement run trace and operational visibility
- WO-CAP-06-09 — Publish and verify PRC-04 test definitions
- WO-CAP-06-10 — Accept CAP-06 on local staging

Key acceptance:

- start returns 202 and run ID;
- same idempotency key and equivalent request returns the same run;
- conflicting reuse is rejected;
- restart resumes from checkpoint;
- cancellation reaches a defined state;
- completed output matches the published schema.

## CAP-07 workorders

- WO-CAP-07-01 — Implement versioned write policy and default approval
- WO-CAP-07-02 — Implement durable human-task state
- WO-CAP-07-03 — Implement human-task inbox and decision UI
- WO-CAP-07-04 — Implement approval API and audit
- WO-CAP-07-05 — Implement rejection and non-executing timeout paths
- WO-CAP-07-06 — Publish and verify PRC-05 test definitions
- WO-CAP-07-07 — Accept CAP-07 on local staging

Key acceptance:

- task shows input, planned action, scope, and relevant context;
- approval reason is optional;
- rejection reason is mandatory;
- only authorised Administrator can decide;
- duplicate or late decision cannot execute twice;
- timeout never approves.

## Release 0.2 workorders

CAP-08:

- durable parallel and merge
- bounded loops and for-each
- versioned subflows
- explicit fallback
- human input and edit
- complete recovery, compensation, and process tests
- staging acceptance

CAP-09:

- authenticated schedules and event triggers
- replay protection and idempotency
- pause, disable, missed-event, and catch-up policies
- staging acceptance

CAP-10:

- one independently testable connector workorder per target
- shared connector-contract changes isolated from implementations
- staging acceptance after connector compliance and security tests

CAP-11:

- export manifest and compatibility contract
- import preview and conflict handling
- secrets excluded
- ownership and project isolation enforcement
- staging acceptance

## Release 0.3 workorders

CAP-12:

- evaluation dataset schema and provenance
- deterministic runner
- result and evidence model
- staging acceptance

CAP-13:

- calibrated metrics and policy states
- observe, warn, human-review, and block actions
- LLM-judge calibration and limitations
- staging acceptance

CAP-14:

- comparable candidate snapshots
- quality, latency, token, and cost comparison
- reproducibility and export
- staging acceptance

## Workorder readiness contract

Before READY, each catalogue item must be expanded with:

- exact source and approved expectation review;
- affected requirements, ARCH and SEC rules;
- applicable ADRs and patterns from `11-architecture-decisions-and-patterns.md`, including their defined scope and prohibited uses;
- observed repository paths;
- explicit scope and prohibited side effects;
- objective positive, negative, boundary, security, and compatibility criteria;
- named CI stages, BDD scenarios, manual tests, and Softwaretest.it mapping;
- design reference where UI is involved;
- stop conditions;
- evidence and later capability-gate assignment.

Catalogue entries are planning slices, not permission to implement.

The maintainable sources and rendered previews required by WO-CAP-05-03 now exist under `docs/visuals/design`. The workorder remains DRAFT because product-owner approval, logo production variants and rights evidence, accessibility measurement, detailed interaction-state references, and Softwaretest.it manual UI/UX tests are still pending.
