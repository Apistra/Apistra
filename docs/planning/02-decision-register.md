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

The public distribution uses AGPL plus a commercial licence alternative. Legal wording and commercial terms require legal approval.

### DEC-004 — Architecture stack

Status: DECIDED

- Web: React and Next.js with TypeScript
- API and AI components: Python and FastAPI
- Platform database: PostgreSQL
- Initial vector store: Qdrant behind a replaceable port
- Execution: separate workers and a proven durable-execution component selected through an ADR
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

Commercial entitlements are verified locally from a cryptographically signed offline licence file. The AGPL distribution does not require a licence file. Mandatory phone-home verification is prohibited.

### DEC-022 — Visual direction and logo

Status: DECIDED

The existing dark technical workflow-editor direction is the starting visual reference. Existing files under images are the canonical logo inputs. A reversible wordmark, vector master, monochrome variants, favicon, and usage rights record remain design deliverables.

## Decisions delegated to controlled ADRs

### ADR-PENDING-001 — Durable execution engine

Status: BLOCKING for runtime implementation

Select a proven component after a focused evaluation of durability, local and offline deployment, PostgreSQL compatibility, worker model, pause and resume, cancellation, retry semantics, licensing, operability, and recovery. Do not build a bespoke distributed job engine.

### ADR-PENDING-002 — Repository and package layout

Status: DEFAULTED

Default recommendation: a monorepo with independently buildable web, API, worker, contracts, connector SDK, and deployment packages. Confirm in CAP-00 after build-tool evaluation.

### ADR-PENDING-003 — Local event transport

Status: DEFERRED

Prefer the simplest transport supported by the durable engine and local deployment requirements. Do not introduce Kafka or an equivalent platform without a measured requirement.

### ADR-PENDING-004 — Authentication implementation

Status: BLOCKING for identity implementation

Select established password hashing, session, CSRF, recovery, and bootstrap mechanisms. Do not implement custom cryptography or token protocols.

### ADR-PENDING-005 — Commercial feature boundary

Status: BLOCKING before commercial release

Define which rights or services are governed by the commercial licence without degrading the usable AGPL product or creating a mandatory online dependency.

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
