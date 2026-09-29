# Apistra Security Concept

Version: 0.1-draft
Status: DRAFT
Profile: EXTENDED

## 1. Scope and security objectives

This concept covers the product, browser and API surfaces, workers, durable execution, databases, vector storage, connectors, model endpoints, local hosts, containers, CI, artefacts, backups, secrets, Softwaretest.it reporting, and operator access.

Primary objectives:

- Prevent cross-project access and privilege escalation.
- Protect credentials, confidential business data, personal data, source code, regulated data, prompts, and model outputs.
- Prevent unapproved external writes and unrestricted agent network access.
- Preserve integrity and provenance of workflow versions, policies, knowledge, evaluations, and runs.
- Maintain recoverability and accountable audit trails.
- Keep offline installations functional without hidden external dependencies.

## 2. Proposed standards baseline

The exact control selection requires qualified review before READY:

- OWASP ASVS 5.0, proposed Level 2 for web application and API requirements
- OWASP WSTG 4.2 for authorised web test methods
- NIST SSDF 1.1 for secure development
- NIST CSF 2.0 for operational responsibility, detection, response, and recovery
- Suitable CIS Benchmarks for the actual supported host, container, PostgreSQL, and reverse-proxy versions
- SLSA 1.2 concepts for artefact provenance; no SLSA level is claimed

Apistra does not claim certification or complete framework conformity.

## 3. Asset and data inventory

### Product assets

- AST-001 Administrator identity and sessions
- AST-002 Project API keys
- AST-003 Project membership and policy state
- AST-004 Workflow drafts and immutable published versions
- AST-005 Agents, prompts, tools, limits, and endpoint references
- AST-006 Connector configurations and synchronisation cursors
- AST-007 Knowledge documents, metadata, chunks, embeddings, and provenance
- AST-008 Run inputs, outputs, state, attempts, approvals, and audit events
- AST-009 Commercial licence file and trusted verification keys

### Infrastructure and supply-chain assets

- AST-010 Source repository and branch protections
- AST-011 CI identities and workflows
- AST-012 Container images, SBOMs, signatures or provenance, and evidence bundles
- AST-013 Local staging configuration and secrets
- AST-014 PostgreSQL data and backups
- AST-015 Qdrant collections and snapshots
- AST-016 Master key and secret-encryption material
- AST-017 Softwaretest.it token, manifests, and receipts
- AST-018 Logs, metrics, traces, and security findings

Data classes:

- Public: published documentation and intentionally public repository content
- Internal: ordinary configuration and non-sensitive operational metadata
- Confidential: workflow definitions, prompts, code, connector data, and business metadata
- Restricted: secrets, personal data, regulated data, sensitive payloads, security findings, and licence signing material

## 4. Threat model

### THR-001 — Cross-project object access

An authenticated principal manipulates an identifier or background-job message to access another project's resource.

Controls: mandatory verified project context, server-side object authorisation, scoped database queries, worker context propagation, negative isolation tests.

### THR-002 — Prompt or content injection invokes a tool

Untrusted source content attempts to override policy and trigger an external read or write.

Controls: treat model output as untrusted, explicit tool contracts, argument validation, deny-by-default tool rights, approval for writes, egress policy, audit.

### THR-003 — SSRF and internal network discovery

A connector, endpoint, callback, or tool targets loopback, metadata, administrative, or private infrastructure.

Controls: canonical URL parsing, DNS and redirect revalidation, blocked address classes, configured allowlists, network profiles, negative tests.

### THR-004 — Secret disclosure

Credentials appear in logs, prompts, exports, test evidence, error messages, or provider requests.

Controls: encrypted secret store, reference-based use, redaction, payload classification, provider data-flow disclosure, secret scanning, negative canary tests.

### THR-005 — Duplicate external side effects

A retry repeats an external write after an uncertain response.

Controls: operation classification, stable idempotency keys, reconciliation or compensation, human approval, visible attempts.

### THR-006 — Workflow version tampering

A published workflow or dependency is edited after approval.

Controls: immutable snapshots, content digests, append-only version creation, authorisation, audit, integrity tests.

### THR-007 — Stale knowledge disclosure

Deleted or deauthorised source content remains retrievable from vector storage.

Controls: provenance graph, tombstones, deletion workflow, index reconciliation, retrieval denial during inconsistent state, deletion tests.

### THR-008 — Resource exhaustion and cost abuse

A client, workflow, connector, or model endpoint consumes excessive compute, calls, tokens, or money.

Controls: configurable hard and warning limits, concurrency control, rate limiting, timeouts, cancellation, quotas, cost telemetry.

### THR-009 — Supply-chain compromise

Dependency, build action, base image, or CI configuration introduces malicious behaviour or leaks secrets.

Controls: pinned dependencies and actions, protected workflows, untrusted PR isolation, SBOM, dependency and image scanning, provenance, review gates.

### THR-010 — Licence bypass or remote dependency

Licence enforcement either becomes security-by-obscurity or requires an unavailable remote service.

Controls: signed offline licence file, public verification key, fail-safe entitlement handling, audit, no secret signing key in product, no phone-home.

## 5. Identity and authorisation model

Initial human role:

- Administrator: installation administration and all project actions in 0.x.

Technical identities:

- Web session principal
- Project API-key principal
- API service principal
- Worker service principal
- Migration principal
- Backup and restore principal
- CI build principal
- Softwaretest.it reporting principal

Rules:

- Authentication and authorisation are server-side.
- Project-scoped resources require a verified project context.
- API keys are shown once, stored as non-reversible verifiers where possible, scoped, rotatable, revocable, and auditable.
- Service identities have only their operational rights.
- CI from untrusted pull requests receives no staging, registry-write, licence-signing, or Softwaretest.it credentials.
- Revocation must invalidate new requests and bounded active sessions according to the chosen authentication ADR.
- Future roles are introduced through policy evolution, not scattered role-name conditionals.

## 6. Secret and key management

- Secrets are encrypted using a well-reviewed authenticated-encryption library.
- The operator supplies the master key through a protected file or container-secret mount.
- The master key is never stored in PostgreSQL, logs, evidence, backups without its separately protected key process, or repository files.
- Secret values are never returned after creation.
- Export contains secret references and metadata, not values.
- Rotation creates a new version and preserves a bounded recovery path.
- Logs and traces apply structured redaction before persistence.
- Licence verification keys may be public; licence signing keys never enter the product runtime or CI for public pull requests.

## 7. Application and API controls

- Validate all inputs against explicit schemas.
- Enforce output schemas before completing a run.
- Apply object-level and function-level authorisation.
- Protect browser sessions against CSRF and session fixation.
- Escape untrusted content and use safe rendering for Markdown, HTML, code, and model output.
- Restrict uploads by type, size, parser, path, and decompression limits.
- Do not expose provider or stack details in client errors.
- Rate-limit authentication, Process API, callbacks, connectors, and administrative operations.
- Require idempotency keys for asynchronous start and declared external effects.
- Sign callbacks and protect them from replay.
- Treat all model output and retrieved content as untrusted data.

## 8. Network and connector controls

Network profiles:

- offline: no external destinations; only explicitly configured local services
- on-premise: approved private and local destinations
- online: approved external providers and connector targets

Agent code has no general network client. Model calls, embeddings, connectors, callbacks, and tools use governed adapters.

Destination validation must be repeated after DNS resolution and redirect. Loopback, link-local, metadata, administrative, and disallowed private ranges are blocked unless an Administrator explicitly configures the applicable on-premise rule and the request still passes policy.

Built-in connectors run with declared permissions and limits. Third-party connector execution is deferred until signing and isolation are designed and tested.

## 9. Data, retention, deletion, and backups

- Metadata and audit retention are configurable.
- Payload retention is independently configurable.
- Sensitive payloads can be processed without persistence where compatible with the workflow contract.
- Project export and deletion are auditable operations.
- Knowledge deletion covers source records, extracted documents, chunks, embeddings, caches, and retrieval eligibility.
- Backups are encrypted, integrity-checked, access-controlled, and restored in drills.
- RPO and RTO remain BLOCKING decisions before production operation.
- Logs never become an uncontrolled payload archive.

## 10. Container, host, and runtime controls

- Containers run as non-root where supported and require no Docker socket.
- Filesystems are read-only except declared state or temporary paths.
- Linux capabilities, mounts, networks, ports, and resources are minimal.
- Services use distinct credentials and database rights where the deployment allows.
- PostgreSQL and Qdrant are not publicly exposed by default.
- Health checks do not disclose secrets or protected data.
- Local staging uses isolated Compose names, networks, volumes, credentials, and synthetic data.
- Host hardening is version-specific and must be validated before operational claims.

## 11. Supply-chain controls

- Protect test, staging, and main branches with pull-request review and required checks.
- Pin third-party GitHub Actions to immutable revisions.
- Generate a candidate-bound SBOM.
- Scan source, dependencies, secrets, containers, and deployment configuration.
- Preserve failed, skipped, cancelled, and error results.
- Build once and promote the same image digest.
- Gate changes to CI and security policy separately from ordinary feature code.
- No public-pull-request job may access protected secrets.

## 12. Detection, response, and recovery

Security events include authentication failures, authorisation denials, key lifecycle, policy changes, workflow publication, approval decisions, external writes, connector changes, licence verification failures, and administrative export or deletion.

Audit events record actor reference, project, operation, resource, result, time, correlation ID, and policy version without sensitive payloads.

An incident runbook must cover credential compromise, suspicious connector or model endpoint, cross-project exposure, malicious workflow, compromised image, backup recovery, and controlled re-release.

## 13. Binding SEC rules

SEC-001 — Deny cross-project access
- Project-scoped operations must verify ownership using the authenticated context.
- Positive own-project and negative foreign-project tests are mandatory.

SEC-002 — Protect secrets by reference
- Secret values must not appear in persisted definitions, logs, exports, evidence, or client responses.
- Canary-secret tests must prove redaction.

SEC-003 — Default approval for writes
- External write tools must pause for human approval unless an active versioned policy explicitly permits the exact action and scope.
- Timeout must never approve.

SEC-004 — Restrict egress
- Runtime network access must be limited to configured destinations and must block protected address classes.
- DNS rebinding and redirect tests are mandatory.

SEC-005 — Immutable publication
- Published workflow snapshots must reject in-place mutation.

SEC-006 — Safe retries
- Automatic retry is allowed only for operations declared safe or protected by verified idempotency.

SEC-007 — Bounded resources
- Every run is subject to configured duration, call, token, cost, concurrency, and rate limits.

SEC-008 — Secure local authentication
- Passwords use an established memory-hard password hashing scheme selected by ADR; sessions are revocable and browser protections apply.

SEC-009 — API-key lifecycle
- Project API keys are scoped, non-recoverable after display, rotatable, revocable, and logged by identifier only.

SEC-010 — Provenance and deletion
- Retrieval results retain source provenance and deleted content cannot remain eligible for retrieval.

SEC-011 — Protected build credentials
- Untrusted code cannot access deployment, registry-write, reporting, or signing secrets.

SEC-012 — Evidence confidentiality
- Test and security evidence is classified, redacted, and disclosed only to authorised readers.

SEC-013 — Offline integrity
- An offline-configured installation must not attempt hidden external communication.

SEC-014 — Signed commercial licence
- Commercial entitlements are accepted only from a correctly signed, valid offline licence document; failure must not expose signing material.

SEC-015 — Audit critical decisions
- Workflow publication, policy change, approval, rejection, external write, key lifecycle, and administrative data actions require attributable audit events.

SEC-016 — Safe callback delivery
- Callbacks are allowlisted, signed, replay-resistant, bounded, and SSRF-protected.

## 14. Security verification

Required automated or authorised tests include:

- own-project and cross-project CRUD and search
- anonymous, invalid, expired, and revoked identity cases
- direct API and object-reference manipulation
- mass assignment and force-browsing cases
- SSRF, redirect, DNS-change, metadata, and loopback cases
- prompt injection attempting unauthorised tool use
- write approval, exception policy, rejection, and timeout
- idempotency under uncertain external response
- secret redaction and export
- stale-vector deletion and retrieval denial
- rate, cost, duration, and concurrency enforcement
- session and API-key revocation
- offline start and execution
- backup integrity and restore
- dependency, secret, container, and deployment scans
- allowed and forbidden architecture/security fixtures for the test tooling

No active security test may target a system without explicit authorisation, limits, synthetic data, and recovery conditions.

## 15. Findings and acceptance

Confirmed cross-project access, privilege escalation, active secret exposure, unapproved external write, critical exploitable dependency, or loss of durable run integrity blocks the affected gate.

Provider limitations may be accepted only by an authorised human with scope, evidence, strongest available configuration, compensating controls, and review triggers. The unsupported control remains visible and is not reported as PASS.

No security evidence currently exists. All SEC rules are planned, not proven.
