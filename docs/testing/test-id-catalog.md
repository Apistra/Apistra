# Canonical Test ID Catalogue

Version: 0.7-draft
Status: DRAFT

## 1. Purpose and authority

This catalogue is the single namespace authority for cross-workorder behavioural scenarios and process-level manual test packages. A workorder may reference only an identifier defined here. The owning test-definition-and-publication workorder must turn the listed intent into executable or manually executable test definitions before dependent implementation becomes READY.

Generated capability or workorder aliases such as `BDD-CAP-*`, `BDD-WO-*`, and `MT-CAP-*` are prohibited. Ranges and wildcards are explanatory shorthand only and are not test identifiers.

## 2. Behavioural scenario catalogue

### Foundation, administration, and projects

- `BDD-OFFLINE-001` — Start and exercise the configured local platform without a required external SaaS dependency.
- `BDD-AUTH-001` — Bootstrap one local Administrator, authenticate, and revoke the session safely.
- `BDD-PROJ-001` — Create an isolated project and deny access from an unrelated project context.
- `BDD-ENDPOINT-001` — Configure and validate an AI endpoint without exposing stored credentials.
- `BDD-LIMIT-001` — Stop a run safely when its configured hard resource or cost limit is reached.

### Knowledge and connectors

- `BDD-KNOW-001` — Synchronise and retrieve knowledge with source and chunk provenance.
- `BDD-KNOW-002` — Delete a source and prove that its removed content is no longer retrievable.

### Workflow authoring and execution

- `BDD-WF-001` — Round-trip one canonical workflow through visual and YAML or JSON representations without semantic drift.
- `BDD-WF-002` — Publish an immutable workflow version and reject mutation of the published snapshot.
- `BDD-RUN-001` — Accept a valid process request asynchronously and return a stable run identity.
- `BDD-RUN-002` — Replay the same idempotency key without duplicating the run or external effects.
- `BDD-RUN-003` — Resume a long-running process from its durable checkpoint after interruption.
- `BDD-APPROVAL-001` — Approve a pending action and resume only the authorised continuation.
- `BDD-APPROVAL-002` — Reject a pending action with a recorded reason and no protected side effect.
- `BDD-APPROVAL-003` — Let an approval expire without silently executing the protected action.

### Advanced flow and triggers

- `BDD-FLOW-001` — Execute parallel branches and merge their declared outputs deterministically.
- `BDD-FLOW-002` — Enforce bounded loop or for-each execution and stop at its declared limit.
- `BDD-FLOW-003` — Invoke a pinned, versioned subflow without changing the caller contract.
- `BDD-FLOW-004` — Apply a declared fallback only for its classified failure condition.
- `BDD-FLOW-005` — Suspend durably for human input and resume with validated input.
- `BDD-FLOW-006` — Suspend durably for human edit and preserve both original and approved revisions.
- `BDD-TRIGGER-001` — Create a scheduled run exactly according to its versioned schedule and timezone contract.
- `BDD-TRIGGER-002` — Accept an authenticated event once and handle replay idempotently.
- `BDD-TRIGGER-003` — Pause or disable a trigger without accepting new executions.
- `BDD-TRIGGER-004` — Apply the configured bounded catch-up policy to missed trigger events.

### Portability and evaluations

- `BDD-PORTABLE-001` — Export a portable definition without secret values or installation-local credentials.
- `BDD-PORTABLE-002` — Preview an import and its changes without mutating project state.
- `BDD-PORTABLE-003` — Reject incompatible versions or unresolved conflicts with actionable diagnostics.
- `BDD-PORTABLE-004` — Import into the selected project without crossing project boundaries.
- `BDD-EVAL-001` — Create an immutable, versioned evaluation dataset with provenance.
- `BDD-EVAL-002` — Run an evaluation deterministically from pinned inputs and record its evidence identity.
- `BDD-EVAL-003` — Apply calibrated observe, warn, review, or block policy actions without implicit escalation or bypass.
- `BDD-EVAL-004` — Compare pinned candidates reproducibly and preserve the comparison inputs and result.

### Enterprise, plugins, deployment, and licensing

- `BDD-IAM-001` — Apply project membership and role changes without granting cross-project access.
- `BDD-IAM-002` — Authenticate through a configured OIDC provider with validated issuer and audience.
- `BDD-IAM-003` — Link an enterprise identity and establish a project-scoped session safely.
- `BDD-IAM-004` — Revoke membership or identity access and invalidate affected authorisation promptly.
- `BDD-IAM-005` — Enforce configured separation-of-duties constraints on protected actions.
- `BDD-PLUGIN-001` — Verify a signed plugin package and reject an untrusted or modified package.
- `BDD-PLUGIN-002` — Validate declared permissions and platform compatibility before installation.
- `BDD-PLUGIN-003` — Install or update a plugin atomically with a defined rollback path.
- `BDD-PLUGIN-004` — Execute plugin code inside its declared isolation and permission boundary.
- `BDD-PLUGIN-005` — Revoke a plugin and apply the documented policy to in-flight work.
- `BDD-K8S-001` — Deploy the supported Kubernetes topology with validated configuration and secret references.
- `BDD-K8S-002` — Upgrade, roll back, and restore the supported profile without losing required state.
- `BDD-K8S-003` — Enforce the supported hardening, health, and readiness contract.
- `BDD-LIC-001` — Validate a commercial licence offline with explicit valid, expired, and invalid outcomes.
- `BDD-LIC-002` — Expose licence status and administration without leaking signed licence material.
- `BDD-LIC-003` — Keep the applicable noncommercial or evaluation path functional without mandatory online activation.
- `BDD-MANAGED-001` — Enforce the documented privacy, tenancy, and responsibility boundary of an optional managed service.

## 3. Manual package catalogue

- `MTP-PRC-01` — Administration and project lifecycle; CAP-01 and CAP-02.
- `MTP-PRC-02` — Connector ingestion, provenance, retrieval, and deletion; CAP-03, CAP-04, and CAP-10.
- `MTP-PRC-03` — Visual and text workflow authoring and immutable publication; CAP-05.
- `MTP-PRC-04` — Asynchronous process API, durable execution, limits, cancellation, and recovery; CAP-06.
- `MTP-PRC-05` — Human approval, rejection, timeout, and audit; CAP-07.
- `MTP-PRC-06` — Evaluation datasets, gates, and candidate comparison; CAP-12 through CAP-14.
- `MTP-PRC-07` — Local packaging, staging, recovery, and offline operation; CAP-00 and operations.
- `MTP-PRC-08` — Advanced durable flow constructs; CAP-08.
- `MTP-PRC-09` — Schedules and authenticated event triggers; CAP-09.
- `MTP-PRC-10` — Secret-safe import, export, and templates; CAP-11.
- `MTP-PRC-11` — Enterprise identity and role administration; CAP-15.
- `MTP-PRC-12` — Signed plugin lifecycle and isolation; CAP-16.
- `MTP-PRC-13` — Supported Kubernetes deployment and recovery; CAP-17.
- `MTP-PRC-14` — Commercial licensing and optional managed-service boundary; CAP-18.

## 4. Individual manual case allocation

An individual manual case receives the immutable format `MT-PRC-NN-NNN`, where `NN` identifies its package and `NNN` is a zero-padded sequence allocated by that capability's test-definition-and-publication workorder. Allocation requires a complete procedure, prerequisites, data, objective oracle, cleanup, evidence fields, reviewer, and a successful Softwaretest.it field-level write/read verification before publication is considered verified.

Allocated `MTP-PRC-01` definitions:

- [`MT-PRC-01-001`](manual/PRC-01/MT-PRC-01-001.md) — Create the single bootstrap Administrator; `DRAFT`, `NOT PUBLISHED`, `NOT EXECUTED`.
- [`MT-PRC-01-002`](manual/PRC-01/MT-PRC-01-002.md) — Do not expose a second Administrator bootstrap after completion; `DRAFT`, `NOT PUBLISHED`, `NOT EXECUTED`.
- [`MT-PRC-01-003`](manual/PRC-01/MT-PRC-01-003.md) — Reject invalid credentials without account disclosure; `DRAFT`, `NOT PUBLISHED`, `NOT EXECUTED`.
- [`MT-PRC-01-004`](manual/PRC-01/MT-PRC-01-004.md) — Revoke a session on sign-out and reject its reuse; `DRAFT`, `NOT PUBLISHED`, `NOT EXECUTED`.
- [`MT-PRC-01-005`](manual/PRC-01/MT-PRC-01-005.md) — Create an isolated project and verify its attributable audit event; `DRAFT`, `NOT PUBLISHED`, `NOT EXECUTED`.
- [`MT-PRC-01-006`](manual/PRC-01/MT-PRC-01-006.md) — Deny direct access to a foreign project without disclosure; `DRAFT`, `NOT PUBLISHED`, `NOT EXECUTED`.

These IDs are now reserved and must not be renamed or reused. Their proposed UI labels derive from design revision `0.3-proposed`; design approval, executable fixture generation, Softwaretest.it publication, field-level read-back, execution, and acceptance remain separate gates.

Implementation workorders reference the package only. Acceptance workorders execute the exact published case IDs; they must not create IDs during execution.

## 5. Governance and traceability

- Renaming or reusing an ID is forbidden. Obsolete IDs remain reserved and receive an explicit retirement record.
- A changed intent requires impact analysis for every referencing workorder and prior result.
- Every execution binds the exact definition revision, repository candidate, environment, attempt, and evidence receipt.
- The process mapping is maintained in [Traceability and Gates](../planning/10-traceability-and-gates.md).
- Test ownership, independence, and evidence rules are maintained in the [Test Concept](test-concept.md).
