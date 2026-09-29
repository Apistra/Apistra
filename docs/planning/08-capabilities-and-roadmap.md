# Capabilities and Gate-Based Roadmap

Version: 0.1-draft
Status: DRAFT

The roadmap has no dates. Progress depends on evidence gates, not elapsed time.

## Release 0.0 — Delivery foundation

### CAP-00 — Reproducible delivery walking skeleton

Outcome:

A maintainer can build an immutable minimal candidate, run the complete bootstrap checks, manually deploy that candidate to isolated local staging, diagnose it, recover it, and report results without any business functionality.

Gate:

- Complete CAP-00 test matrix passed
- Exact candidate deployed locally
- Recovery demonstrated
- Softwaretest.it publishing readiness passed
- Human bootstrap acceptance

## Release 0.1 — Governed end-to-end AI process

### CAP-01 — Installation and isolated project administration

Outcome:

An Administrator can bootstrap an offline-capable installation and manage isolated projects with audited configuration.

### CAP-02 — Secrets, endpoints, agents, tools, and limits

Outcome:

An Administrator can configure protected secrets, model and embedding endpoints, versioned agents, governed tools, and configurable resource limits.

### CAP-03 — Connector foundation and trusted sources

Outcome:

An Administrator can configure and synchronise file or directory, REST, and Git sources through a versioned public connector contract.

### CAP-04 — Knowledge and cited retrieval

Outcome:

An Administrator can create knowledge sources, index them, retrieve cited content, and reliably remove stale derived data.

### CAP-05 — Workflow authoring and publication

Outcome:

An Administrator can author the same workflow visually and as YAML or JSON, validate and test it, and publish an immutable version.

0.1 node set:

- Input
- Output
- Agent
- Retrieval
- Tool
- Transform
- Validation
- Decision
- Human Approval
- Retry
- explicit error path

### CAP-06 — Durable Process API

Outcome:

An API client can start, observe, cancel, and obtain results from a durable, idempotent, schema-valid workflow run.

### CAP-07 — Human approval and controlled writes

Outcome:

A writing action pauses safely, is approved or rejected through the inbox or API, and resumes or terminates with complete auditability.

### 0.1 release gate

- CAP-00 through CAP-07 accepted
- Offline local demonstration succeeds
- Required manual process packages pass
- All automated results are confirmed in Softwaretest.it
- No blocking architecture or security finding
- AGPL and commercial licensing texts receive legal approval
- Public documentation and brand asset gate pass

## Release 0.2 — Advanced orchestration and integrations

### CAP-08 — Advanced control flow

Outcome:

Workflow authors can use parallel and merge, loops and for-each, subflows, fallback, human input, and human edit while preserving durability and versioning.

### CAP-09 — Scheduled and event-triggered execution

Outcome:

Administrators can configure scheduled or event-triggered runs with authenticated sources, replay protection, and limits.

### CAP-10 — Expanded connector catalogue

Outcome:

Administrators can connect S3-compatible storage, PostgreSQL, websites, Jira, and Confluence through the same contract and provenance model.

### CAP-11 — Import, export, and templates

Outcome:

Administrators can move reviewed project assets between installations without exporting secrets or violating ownership.

### 0.2 release gate

- Advanced control-flow recovery and compensation proven
- Connector security and incremental-sync contract proven
- Import and export isolation proven
- 0.1 regression gate passes on the unchanged candidate

## Release 0.3 — Evaluation and AI quality

### CAP-12 — Versioned evaluation datasets

Outcome:

AI engineers can define versioned test cases and expected properties for workflows and agents.

### CAP-13 — Evaluation gates

Outcome:

Teams can observe, warn, request review, or block based on calibrated deterministic and AI-assisted policies.

### CAP-14 — Candidate comparison

Outcome:

AI engineers can compare model, prompt, agent, retrieval, and workflow candidates using quality, cost, and latency evidence.

### 0.3 release gate

- Evaluation dataset provenance proven
- LLM-judge calibration and limitations documented
- No uncalibrated judge acts as sole blocking authority
- Regression and comparison results are reproducible

## Later 0.x

### CAP-15 — Role-based administration and enterprise identity

Additional roles, OIDC or SSO, project membership, and separation of duties.

### CAP-16 — Trusted third-party plugin execution

Signed plugins, declared permissions, compatibility contract, resource isolation, and revocation.

### CAP-17 — Kubernetes deployment profile

Operationally supported Kubernetes packaging without weakening the Compose baseline.

### CAP-18 — Commercial operations and optional managed service

Commercial entitlements, support operations, managed hosting boundaries, and production environment contracts.

## Cross-capability gate rules

- One active capability and at most one or two independent active workorders are the default until review capacity is demonstrated.
- Blocked work and waiting reviews count as work in progress.
- Every capability has one final staging acceptance workorder.
- Changes to shared foundations may invalidate evidence for later capabilities.
- No capability is accepted from partial green evidence or a percentage score.
