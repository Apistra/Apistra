# Product Scope

Version: 0.1-draft
Status: DRAFT
Product: Apistra

## 1. Problem

Organisations increasingly need AI-assisted business processes that combine model calls, private knowledge, deterministic processing, external systems, and accountable human decisions. Existing solutions often bind workflows to one model provider, hide execution state, treat RAG as an isolated feature, or expose insufficiently governed APIs.

Apistra addresses this by making workflows explicit, versioned, testable, auditable, and operable across cloud and on-premise environments.

## 2. Primary users

- Developers integrating business processes through APIs
- AI engineers configuring models, prompts, tools, retrieval, and evaluations
- Technical solution architects designing reliable cross-system processes
- Administrators operating an installation and controlling projects, endpoints, secrets, policies, and licences

The initial product role is Administrator. The architecture must not hard-code this as the permanent role model.

## 3. Value proposition

Apistra enables a technical team to:

- connect external systems through a public connector contract;
- configure cloud or on-premise AI endpoints without binding agents to one provider;
- ingest distributed knowledge and retain source provenance;
- design workflows visually and through canonical YAML or JSON;
- publish immutable workflow versions;
- execute them asynchronously through a stable API;
- pause safely for human approval;
- understand status, retries, model usage, cost, evidence, and outcomes;
- operate offline when all configured dependencies are local.

## 4. Core product journeys

### PRC-01 — Configure an installation and project

An Administrator signs in, creates or selects a project, configures secrets and model endpoints, and establishes project limits and policies.

### PRC-02 — Connect and index knowledge

An Administrator configures a source, runs or schedules synchronisation, observes extraction and indexing, and verifies source-level provenance and deletion behaviour.

### PRC-03 — Author and publish a workflow

An Administrator creates a draft visually or as YAML or JSON, configures nodes, validates the graph, tests it, and publishes an immutable version.

### PRC-04 — Execute a published process through the API

An API client starts a run with an idempotency key, receives a run identifier, observes progress, obtains the final result, or requests cancellation.

### PRC-05 — Complete a human approval

An Administrator sees the pending task, its input and planned action, approves or rejects it with the required reason, and the durable run resumes or terminates.

### PRC-06 — Evaluate workflow quality

An AI engineer executes versioned test datasets, compares candidates, reviews cost and quality results, and applies a calibrated release policy.

### PRC-07 — Operate and recover Apistra

An Administrator observes health and runs, backs up state, restores it, and diagnoses or recovers a failed deployment without losing auditability.

### Later 0.x journeys

- PRC-08 — Author and recover advanced control flow: an Administrator uses bounded parallelism, loops, subflows, fallback, human input, and human edit while retaining deterministic recovery.
- PRC-09 — Configure scheduled or event-triggered execution: an Administrator creates, pauses, disables, and diagnoses authenticated triggers with explicit replay and catch-up policy.
- PRC-10 — Move reviewed assets between installations: an Administrator previews, exports, maps, resolves, and imports compatible project assets without secrets.
- PRC-11 — Administer roles and enterprise identity: an authorised identity administrator manages provider configuration, membership, roles, revocation, and separation of duties.
- PRC-12 — Install and govern a trusted plugin: an Administrator verifies provenance, permissions, compatibility, isolation, update, and revocation.
- PRC-13 — Operate the Kubernetes profile: an operator installs, observes, upgrades, restores, and recovers an immutable candidate on a supported Kubernetes environment.
- PRC-14 — Administer commercial operations: an authorised operator applies an offline licence, exports a redacted support bundle, and, only under a separate approved contract, operates a managed-service environment.

## 5. Product scope

### Initial 0.x product arc

- One organisation per installation
- Multiple strictly isolated projects
- Local Administrator authentication
- Configurable model and embedding endpoints
- OpenAI and generic OpenAI-compatible endpoint adapters first
- Project-scoped encrypted secrets
- Connector SDK and trusted built-in connectors
- File or directory, REST, and Git connectors first
- Full ingestion and RAG pipeline with replaceable vector-store boundary
- PostgreSQL for platform state and Qdrant as the first vector store
- Visual editor plus canonical YAML or JSON representation
- Draft and immutable published workflow versions
- Agent, retrieval, tool, transform, validation, decision, human approval, retry, input, and output nodes in 0.1
- Durable asynchronous execution and generated process API
- Status, result, cancellation, callback or webhook, project API keys, and idempotency
- Configurable resource, token, cost, concurrency, and rate limits
- Local inbox and API for human approval
- Local-first logs, metrics, traces, and audit records
- Docker Compose as the first fully supported deployment model
- Air-gap-compatible operation when dependencies are local

### Later 0.x scope

- Parallel and merge nodes
- Loops and for-each
- Subflows
- Explicit fallback
- Human input and human edit
- Schedules and events
- Evaluation gates and versioned evaluation datasets
- Model and workflow comparisons
- Additional connectors including S3-compatible storage, PostgreSQL, websites, Jira, and Confluence
- Trusted third-party plugins with signing, permission declaration, compatibility checks, and isolation
- Additional roles and enterprise identity
- Kubernetes deployment profile
- Managed hosting option

## 6. Non-goals for the first release slice

- Hosting, downloading, or scaling model weights
- Automatic production deployment
- Public connector marketplace
- Arbitrary third-party plugin execution
- Cross-organisation multi-tenancy in one installation
- Automatic acceptance of AI-generated evaluations as the sole release authority
- Certification claims
- A general-purpose BPM suite unrelated to AI-assisted processes
- A no-code promise for non-technical users

## 7. Binding product rules

- A draft is mutable; a published workflow version is immutable.
- Every run is bound to a complete versioned snapshot of workflow, agent, prompt, tool, knowledge, and policy references.
- Secrets are referenced, never copied into snapshots, logs, exports, or evidence.
- Older published versions remain callable until explicitly disabled.
- Every agent has one versioned primary model endpoint and may have one explicit fallback endpoint.
- Dynamic model routing is deferred.
- Writing tools require human approval by default.
- An Administrator may publish a narrower explicit policy that permits a named tool action within a defined project and scope.
- A timeout never grants approval.
- Agent network access is denied except through configured endpoints and tools.
- RAG results retain document, version, location, and derived-chunk provenance.
- Removing or disabling a source removes or deactivates its derived chunks and embeddings.
- Missing citations can be configured to continue, warn, require approval, or block.
- Limits are present from the start and configurable by installation, project, workflow, and where applicable agent.
- No external telemetry is enabled by default.

## 8. Commercial and licensing model

The public repository is transitioning from AGPL to a source-available model for future releases. PolyForm Noncommercial 1.0.0 covers its defined noncommercial purposes. PolyForm Free Trial 1.0.0 covers a 32-day company evaluation without distribution. Productive commercial use, internal business operation, commercial integration, redistribution, resale, SaaS, and managed-service operation require a separately signed Apistra Commercial License. Mandatory phone-home communication is prohibited; a signed offline licence file may carry machine-verifiable commercial entitlements but does not replace the legal agreement.

Already published AGPL versions remain available under their existing grant. The repository `LICENSE`, copyright notice, commercial terms, rights-holder identity, and exact transition boundary implement ADR-022; `LICENSE-TRANSITION.md` is the canonical boundary record.

## 9. Success criteria

The product arc is successful when a new installation can reproducibly:

1. create an isolated project;
2. configure a local or remote model endpoint and secrets;
3. ingest a source and retrieve cited knowledge;
4. author and publish a workflow;
5. start a durable run through the API;
6. pause at a human approval and resume safely;
7. return a schema-valid result with traceable execution evidence;
8. respect configured limits and network policy;
9. recover from a controlled failure without losing run integrity;
10. prove the candidate through the defined local staging and test gates.
