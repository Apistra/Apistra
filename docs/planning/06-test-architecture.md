# System-Centred Test Architecture

Version: 0.1-draft
Status: DRAFT

## 1. Test purpose and scope

Testing must demonstrate that Apistra preserves project isolation, executes versioned workflows durably, applies human and automated policy correctly, exposes stable APIs, manages knowledge provenance, operates offline, and can be delivered and recovered reproducibly.

Implementation-derived tests are not the sole authority. Expected behaviour is derived from the approved product, architecture, security, delivery, and design contracts.

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

## 4. Critical process models

### PRC-03 — Author and publish

P03-S01 Start draft
P03-S02 Edit graph or canonical text
P03-S03 Validate schema and references
P03-G01 Valid?
P03-S04 Execute draft test
P03-G02 Test acceptable?
P03-S05 Publish immutable version
P03-E01 Published
P03-E02 Validation or test rejected

### PRC-04 — Execute Process API

P04-S01 Authenticate project API key
P04-S02 Validate workflow version, input, idempotency, and limits
P04-G01 Existing idempotent run?
P04-S03 Create durable run
P04-S04 Execute nodes and checkpoints
P04-G02 Human task required?
P04-S05 Wait and resume
P04-G03 Completed, failed, or cancelled?
P04-S06 Validate result
P04-S07 Deliver optional callback
P04-E01 Result available
P04-E02 Failed or cancelled with safe evidence

### PRC-05 — Human approval

P05-S01 Create pending task
P05-S02 Present input, planned action, scope, and context
P05-G01 Approve, reject, or timeout?
P05-S03 Record approval and resume
P05-S04 Record rejection reason and terminate configured path
P05-S05 Apply non-executing timeout path
P05-E01 Resumed
P05-E02 Rejected
P05-E03 Timed out without action

### PRC-02 — Knowledge synchronisation

P02-S01 Start manual or scheduled sync
P02-S02 Enumerate changes
P02-S03 Extract and normalise
P02-S04 Chunk and embed
P02-S05 Upsert index and provenance
P02-G01 Removed content?
P02-S06 Delete or deactivate derived records
P02-E01 Consistent source version
P02-E02 Retryable failure with cursor retained

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
- Automated tests: NOT IMPLEMENTED
- Manual test definitions: NOT YET EXPANDED
- Fixtures: NOT IMPLEMENTED
- Softwaretest.it project and plan: NOT CREATED OR VERIFIED
- Test execution: NOT STARTED
- Capability acceptance: BLOCKED

## 14. Review obligations

EXTENDED assurance requires:

- independent derivation of critical expectations;
- product-owner confirmation of critical behaviour;
- independent implementation review against the approved specification;
- preservation of contradictory or failed evidence;
- separate human capability acceptance.
