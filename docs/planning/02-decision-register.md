# Decision Register

Version: 0.1-draft
Status: DRAFT

## Confirmed product decisions

### DEC-001 — Greenfield implementation

Status: DECIDED

Apistra is implemented as a new product with high code-quality requirements. The existing research application is a behavioural and visual reference only. Its code is not a foundation and must not be copied without a separately reviewed reason.

### DEC-002 — Public build and contribution policy

Status: DECIDED

The repository is public and developed in public. External contributions are not accepted initially. Contribution governance and any CLA or DCO process are deferred.

### DEC-003 — Licensing

Status: DECIDED

Apistra is developed in public as source-available software. PolyForm Noncommercial 1.0.0 covers its permitted noncommercial purposes; PolyForm Free Trial 1.0.0 permits company evaluation for fewer than 32 consecutive calendar days; productive commercial use, internal business operation, commercial integration, redistribution, resale, SaaS, or managed-service operation requires a separately signed Apistra Commercial License. This is not represented as OSI-approved Open Source. Jens Bekersch is the licensor and copyright holder. Previously published AGPL versions retain their granted rights. `LICENSE-TRANSITION.md` records the exact boundary, notice, and contact details.

### DEC-004 — Architecture stack

Status: DECIDED

- Web: React and Next.js with TypeScript
- API and AI components: Python and FastAPI
- Platform database: PostgreSQL
- Initial vector store: Qdrant behind a replaceable port
- Execution: separate workers and an Apistra-owned durable-execution runtime; no external orchestration product or control plane is a runtime prerequisite
- Packaging: container images and Docker Compose

### DEC-005 — Deployment topology

Status: DECIDED

Docker Compose is the first supported deployment model. One installation serves one organisation and multiple isolated projects. Kubernetes and managed hosting are later profiles.

### DEC-006 — Offline operation

Status: DECIDED

Apistra must run without external dependencies when configured endpoints and data sources are local. External telemetry is opt-in only.

### DEC-007 — Workflow representation

Status: DECIDED

The visual editor and YAML or JSON operate on one canonical versioned workflow model. Published versions are immutable.

### DEC-008 — Process API

Status: DECIDED

Every published workflow version can expose a versioned API with validated input and output, asynchronous start returning 202 and a run ID, status, result, cancellation, optional callback, project API keys, and idempotency.

### DEC-009 — Identity

Status: DECIDED

The first release uses a local bootstrap Administrator account suitable for offline operation. The identity boundary must support later OIDC or SSO without replacing domain rules.

### DEC-010 — Secret protection

Status: DECIDED

Secrets are encrypted at rest using established cryptographic libraries and an operator-provided master key. The key is supplied as a protected file or container secret and never stored in the application database or repository.

### DEC-011 — Model endpoints

Status: DECIDED

Apistra connects to managed model servers; it does not manage model weights. Each agent version has one primary endpoint and may have one explicit fallback.

### DEC-012 — Project isolation

Status: DECIDED

Connectors, secrets, knowledge, agents, workflows, runs, API keys, policies, limits, and audit data are project-scoped. Cross-project access is denied by default.

### DEC-013 — Connectors

Status: DECIDED

A public connector contract exists from the start. Only trusted built-in connectors execute initially. File or directory, REST, and Git are first.

### DEC-014 — Knowledge ownership

Status: DECIDED

Apistra owns extraction, parsing, cleaning, metadata, chunking, embeddings, indexing, updates, deletion, retrieval, and citations. Embedding endpoints are configurable per knowledge source.

### DEC-015 — Human approval policy

Status: DECIDED

Writing tools require human approval by default. An Administrator can publish an explicit versioned exception for a named action and scope. Rejection requires a reason. Timeout never executes the action.

### DEC-016 — Network policy

Status: DECIDED

Agents have no arbitrary outbound access. Network operations pass through configured endpoints or tools, with protection for loopback, metadata, administrative, and internal targets. Online, on-premise, and offline profiles are supported.

### DEC-017 — Evaluation policy

Status: DECIDED

Deterministic technical and schema gates may block from 0.1. AI-based evaluation policies arrive in 0.3 and may observe, warn, request human review, or block only after calibration. An uncalibrated LLM judge cannot be the sole release authority.

### DEC-018 — Branch and promotion model

Status: DECIDED

Feature branches merge through pull requests into test, then staging, then main. No branch automatically deploys anywhere. The unchanged candidate is manually deployed to an isolated local staging profile for acceptance before promotion.

### DEC-019 — Roadmap

Status: DECIDED

The roadmap is gate-based, not date-based.

### DEC-020 — Documentation and localisation

Status: DECIDED

All repository documentation, code identifiers, APIs, workorders, test definitions, and issues use English. The UI is internationalised from the beginning with English and German as the first locales.

### DEC-021 — Licence verification

Status: DECIDED

The noncommercial and evaluation distributions do not require online activation. Where a commercial agreement grants machine-verifiable entitlements, they are verified locally from a cryptographically signed offline licence file. Mandatory phone-home verification is prohibited. Contractual licence rights and technical entitlements remain distinct.

### DEC-022 — Visual direction and logo

Status: DECIDED

The existing dark technical workflow-editor direction is the starting visual reference. Existing files under images are the canonical logo inputs. A reversible wordmark, vector master, monochrome variants, favicon, and usage rights record remain design deliverables.

## Decisions delegated to controlled ADRs

### ADR-020 — Apistra-owned durable execution runtime

Status: DECIDED

Apistra owns and implements its durable orchestration runtime. No external workflow engine, orchestration server, hosted control plane, licence service, or paid management product is required for execution, recovery, diagnosis, or offline operation. PostgreSQL is the durable system of record. The runtime is delivered incrementally through persisted state machines, an append-only execution journal, transactional outbox and inbox, lease-based dispatch, idempotency records, durable timers, cancellation, human signals, explicit compensation, versioning, and recovery. Libraries are allowed only when they work offline, are licence-compatible, pinned, inventoried, replaceable behind owned boundaries, and practically forkable or maintainable.

### ADR-019 — Repository and package layout

Status: DECIDED

Use one monorepo with `apps/web`, one installable Python package under `backend`, language-neutral contracts under `contracts`, a separately versioned `connector-sdk/python` boundary, Compose packaging under `deploy/compose`, engineering-only integrations under `engineering`, retained architecture fixtures under `tests/architecture-fixtures`, and repository automation under `tools`. Backend business ownership is module-first with internal layers. Cross-module imports use only `modules.<name>.public`. The complete rationale and dependency rules are recorded in `11-architecture-decisions-and-patterns.md`.

### ADR-PENDING-003 — Local event transport

Status: DEFERRED

Prefer PostgreSQL-backed dispatch within the owned Apistra runtime until measured throughput or isolation requirements justify another locally controlled transport. Do not introduce Kafka or an equivalent platform without a measured requirement and a separate ADR.

### ADR-021 — Local authentication implementation

Status: DECIDED

Release 0.1 uses local Administrator authentication with Argon2id password hashing and opaque server-side sessions stored in PostgreSQL. Browser sessions use secure, HTTP-only, same-site cookies and server-side CSRF protection. The first Administrator is created through a single-use local CLI bootstrap; privileged local recovery replaces any email or online dependency. Sessions are revocable and rotated at security-sensitive transitions. Apistra does not invent cryptography, browser token protocols, or OAuth/OIDC; enterprise identity remains deferred to CAP-15.

### ADR-022 — Source-available and commercial licensing boundary

Status: DECIDED; IMPLEMENTED

Apistra releases from the transition commit use PolyForm Noncommercial 1.0.0 for its permitted noncommercial purposes and PolyForm Free Trial 1.0.0 for company evaluation for fewer than 32 consecutive calendar days. Productive commercial use, internal business operation, commercial integration, redistribution, resale, SaaS, and managed-service operation require a separate licence signed by the licensee and Jens Bekersch. The repository remains public and build-in-public but is described as source available, not OSI Open Source. Existing AGPL grants remain valid for versions already published. `LICENSE`, `NOTICE`, `COMMERCIAL-LICENSE.md`, and `LICENSE-TRANSITION.md` implement the decision without mandatory online activation.

## Explicitly deferred decisions

- Managed hosting provider and region model
- Kubernetes operator or packaging method
- Third-party plugin sandbox technology
- Dynamic model routing
- Enterprise role catalogue
- OIDC provider matrix
- Marketplace governance
- Certification programme
- Production infrastructure
