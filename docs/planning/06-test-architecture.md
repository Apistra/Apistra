# System-Centred Test Architecture

Version: 0.3-draft
Status: DRAFT

## 1. Test purpose and scope

Testing must demonstrate that Apistra preserves project isolation, executes versioned workflows durably, applies human and automated policy correctly, exposes stable APIs, manages knowledge provenance, operates offline, and can be delivered and recovered reproducibly.

Implementation-derived tests are not the sole authority. Expected behaviour is derived from the approved product, architecture, security, delivery, and design contracts.

This document defines the system-centred test architecture: test boundaries, layers, models, and technical evidence paths. The operational rules for planning, executing, evaluating, and accepting tests are defined in the [Test Concept](../testing/test-concept.md).

## 2. System test map

Actors:
- Administrator
- API client
- Human approver
- Maintainer

Core systems:
- Web
- Management API and Process API
- Worker
- Durable engine
- PostgreSQL
- Qdrant
- Model and embedding endpoints
- Connector targets
- Callback receiver

Engineering systems:
- GitHub Actions
- Artefact store
- Softwaretest.it
- Local staging host

## 3. Static test model

System-level tests cover actor-to-system contracts.

Component tests cover:
- workflow schema and validator
- publication service
- run state machine
- policy and approval service
- endpoint adapters
- connectors and synchronisation
- knowledge pipeline and retrieval
- project authorisation
- licence verification
- evidence and reporting adapters

Class-level models are created with implementation and are restricted to architecturally significant classes such as WorkflowDefinition, PublishedWorkflow, AgentVersion, KnowledgeSource, Run, NodeAttempt, HumanTask, PolicyVersion, LimitSet, ConnectorCursor, ProvenanceRecord, and LicenceGrant.

Static architecture references:

- [System context](../visuals/architecture/system-context.svg)
- [Runtime containers](../visuals/architecture/containers.svg)
- [Module dependency direction](../visuals/architecture/module-dependencies.svg)
- [Core domain model](../visuals/architecture/domain-model.svg)

### 3.1 Executable architecture test model

- AT-ARCH-001 checks domain independence with Import Linter and the Python AST rule set.
- AT-ARCH-010 keeps engineering-only Softwaretest.it integration outside the runtime graph.
- AT-ARCH-011 verifies explicit API and worker composition roots and adapter containment.
- AT-ARCH-012 verifies public feature and module contracts.
- AT-ARCH-013 detects dependency cycles in the TypeScript graph and rejects forbidden Python layer direction.
- AT-ARCH-SCOPE rejects an empty source scope.
- AT-ARCH-FIXTURE requires retained allowed graphs to pass and retained forbidden graphs to fail.

The authoritative commands, tool versions, paths, and exception policy are maintained in `docs/architecture/testing.md`. These tests are structural evidence only and cannot substitute for behavioural, integration, security, deployment, or recovery tests.

## 4. Critical process models

The canonical models are versioned BPMN 2.0 files. The SVG and PNG files are generated review views from the same process definitions.

### PRC-01 — Configure installation and project

- [BPMN 2.0 source](../visuals/processes/prc-01.bpmn)
- [Readable process view](../visuals/processes/prc-01.svg)

### PRC-02 — Connect and index knowledge

- [BPMN 2.0 source](../visuals/processes/prc-02.bpmn)
- [Readable process view](../visuals/processes/prc-02.svg)

### PRC-03 — Author and publish a workflow

- [BPMN 2.0 source](../visuals/processes/prc-03.bpmn)
- [Readable process view](../visuals/processes/prc-03.svg)

### PRC-04 — Execute a published process through the API

- [BPMN 2.0 source](../visuals/processes/prc-04.bpmn)
- [Readable process view](../visuals/processes/prc-04.svg)

### PRC-05 — Complete a human approval

- [BPMN 2.0 source](../visuals/processes/prc-05.bpmn)
- [Readable process view](../visuals/processes/prc-05.svg)

### PRC-06 — Evaluate workflow quality

- [BPMN 2.0 source](../visuals/processes/prc-06.bpmn)
- [Readable process view](../visuals/processes/prc-06.svg)

### PRC-07 — Operate and recover Apistra

- [BPMN 2.0 source](../visuals/processes/prc-07.bpmn)
- [Readable process view](../visuals/processes/prc-07.svg)

Every process receives a complete manual process test package even when automated E2E coverage exists.

## 5. Risk priorities

Highest test intensity:

- project isolation
- unapproved writes
- SSRF and unrestricted agent access
- duplicate side effects
- run recovery and approval resumption
- published-version immutability
- secret disclosure
- stale knowledge after deletion
- Process API idempotency
- migration and restore

High:

- schema round-trip
- provider compatibility
- connector incremental sync
- limits and cost enforcement
- callback security
- audit attribution

Medium:

- visual consistency
- localisation completeness
- convenience functions

## 6. Test design

Unit:
- domain invariants, validation, policy, state transitions, limits, parsing, redaction

Component:
- service boundaries with fakes or controlled dependencies

Contract:
- OpenAPI, workflow schema, connector SDK, endpoint adapters, callbacks, events, Softwaretest.it

Integration:
- PostgreSQL transactions and isolation
- Qdrant provenance and deletion
- durable engine checkpoints and retries
- endpoint and connector simulators

Automated BDD E2E:
- critical observable product journeys
- stable BDD IDs and human-readable Given, When, Then

Manual:
- every process package
- all relevant roles, project boundaries, states, errors, viewports, keyboard, screen reader, and recovery

Security:
- authenticated positive and negative controls at actual enforcement points

Resilience:
- service restart, worker loss, timeout, cancellation, uncertain response, recovery

Performance:
- defined synthetic profiles after representative runtime exists

## 7. Initial automated BDD catalogue

BDD-AUTH-001 — Administrator signs in to an offline installation.

BDD-PROJ-001 — Administrator creates an isolated project.

BDD-ENDPOINT-001 — Administrator validates an OpenAI-compatible endpoint without exposing its secret.

BDD-KNOW-001 — Administrator synchronises a source and retrieves an answer with source provenance.

BDD-KNOW-002 — Removed source content is no longer retrievable.

BDD-WF-001 — Administrator round-trips a workflow between visual and canonical representations without semantic change.

BDD-WF-002 — Administrator publishes an immutable valid workflow version.

BDD-RUN-001 — API client starts a run and receives 202 with a run identifier.

BDD-RUN-002 — Repeated start with the same idempotency key returns the same run.

BDD-RUN-003 — Interrupted execution resumes from the committed checkpoint.

BDD-APPROVAL-001 — Writing action pauses until an Administrator approves it.

BDD-APPROVAL-002 — Rejection terminates the configured path and records the reason.

BDD-APPROVAL-003 — Timeout does not execute the action.

BDD-LIMIT-001 — A run stops safely at its configured hard budget.

BDD-OFFLINE-001 — Local workflow execution completes without an external network dependency.

Detailed Given, When, Then definitions are produced in the owning workorder before implementation.

## 8. Manual test contract

Each manual case:

- has a stable MT identifier;
- begins at the local staging login page in a logged-out session;
- uses an automatically prepared synthetic Administrator or API client fixture;
- separates username entry, password entry, login action, and every navigation action;
- contains one action or one observation per step;
- includes explicit data and one directly corresponding expected result;
- contains no plaintext secret;
- records candidate digest, staging target, executor, time, step result, and evidence.

Initial process packages:

- MTP-PRC-01 installation and project administration
- MTP-PRC-02 knowledge synchronisation and deletion
- MTP-PRC-03 workflow authoring, validation, testing, and publication
- MTP-PRC-04 Process API execution, idempotency, cancellation, and result
- MTP-PRC-05 approval, rejection, and timeout
- MTP-PRC-06 evaluation and release policy
- MTP-PRC-07 operation, backup, restore, and recovery

Each package includes happy path, boundaries, invalid inputs, conflicts, retries, timeouts, security, authorisation, accessibility, and relevant combined flows.

## 9. Test data and service virtualisation

- Synthetic project and identities per test run
- Deterministic local model and embedding simulators for contract and failure cases
- Controlled REST, Git, file, callback, and tool targets
- Versioned source documents with additions, updates, and deletions
- Idempotent fixture creation and isolated cleanup
- Protected runtime references for passwords and tokens
- Unique candidate and test-run identifiers

The fixture generator is a CAP-00 deliverable and expands with each capability.

## 10. Softwaretest.it model

Planned external project key: apistra

Before creation, confirm the actual API contract. Do not assume resource names or payload fields.

The synchronisation manifest must preserve:

- capability and process IDs
- BDD IDs
- manual test IDs and ordered atomic steps
- requirement, risk, design, and workorder links
- content versions and checksums
- returned platform IDs and receipts

Definition, publication, fixture readiness, execution, and result reporting are separate states.

## 11. Result reporting

Every CI stage emits immutable machine-readable results. CI-TS-16 reports all statuses and retains:

- candidate digest
- commit and pull request
- stage, suite, test, and attempt
- expected and actual safe summary
- duration and retry metadata
- evidence references
- defect and retest linkage

Reporting failure blocks acceptance but does not invalidate a completed test attempt.

## 12. Observability for testing

Required correlations:

- request ID
- project ID
- workflow and version
- run and node
- attempt
- human task
- connector sync
- candidate digest
- CI stage and attempt
- Softwaretest.it test and run receipt

Logs, metrics, traces, and audit records must allow failure localisation without revealing restricted payloads.

## 13. Test gate status

- Test architecture definition: DRAFT
- Test concept: DRAFT
- CAP-00 automated architecture, contract, unit, integration, BDD, security, recovery, packaging, and evidence checks: IMPLEMENTED AND HOSTED VERIFIED
- Business capability automated tests: NOT IMPLEMENTED
- CAP-00 manual test definition: IMPLEMENTED; independent execution and human acceptance remain PENDING
- Business capability manual packages: NOT YET EXPANDED OR PUBLISHED
- CAP-00 synthetic engineering fixtures: IMPLEMENTED; business fixtures expand with their owning capabilities
- Softwaretest.it public API contract: VERIFIED; authenticated project, plan, and result round-trip remains BLOCKED
- CAP-00 formal acceptance: BLOCKED on repository protection, authenticated Softwaretest.it evidence, independent review, and human acceptance
- Business capability acceptance: NOT STARTED

## 14. Review obligations

EXTENDED assurance requires:

- independent derivation of critical expectations;
- product-owner confirmation of critical behaviour;
- independent implementation review against the approved specification;
- preservation of contradictory or failed evidence;
- separate human capability acceptance.
