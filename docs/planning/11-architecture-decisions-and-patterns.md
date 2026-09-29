# Architecture Decisions and Pattern Catalogue

Version: 0.3-draft
Status: DRAFT
Assurance profile: EXTENDED

This document makes the software-architecture choices operational. Pattern names are not quality claims. Every decision states the concrete problem, scope, simpler alternative, intended use, prohibited use, consequences, and verification.

## ADR-001 — Modular monolith as the 0.x backend system style

Status: PROPOSED

### Context and decision

Apistra has substantial domain boundaries but begins with one product team, one installation model, and a Docker Compose deployment. Independent microservices would add distributed transactions and operational failure modes before independent scaling or ownership requires them.

Use a modular monolith for backend source and domain ownership, deployed through separate API and worker processes from the same versioned backend codebase. The Next.js web application is separate. PostgreSQL is physically shared in 0.x, while each module owns its schema or tables and exposes application contracts.

Modules:

- identity_admin
- projects
- secrets_endpoints
- connectors
- knowledge
- agents_tools
- workflows
- runtime
- human_tasks
- policies_limits
- evaluation
- audit_observability
- licensing

Allowed:

- API and worker composition roots depend on module public application interfaces.
- A module exposes explicit commands, queries, domain events, and DTOs.
- Read-only cross-module projections use a documented query contract.

Prohibited:

- One module reading or writing another module's tables directly.
- Cross-module ORM relationships that bypass ownership.
- Independent network services without an approved scaling or trust-boundary ADR.

Simpler alternative considered:

One undivided application package was rejected because project isolation, workflow publication, knowledge, runtime, and approvals change independently and require enforceable ownership.

Verification:

ARCH-004 and ARCH-013 dependency and data-ownership tests, migration ownership check, and a forbidden cross-module fixture.

## ADR-002 — Ports and Adapters only at volatile or security-relevant boundaries

Status: PROPOSED

### Context and decision

Model providers, embedding providers, vector stores, connectors, durable engines, identity systems, licences, clocks, identifiers, and external tools can vary or introduce vendor-specific semantics.

Use Ports and Adapters for:

- model and embedding execution;
- connector enumeration and content retrieval;
- vector storage;
- durable execution engine;
- secret encryption and key access;
- identity and session provider;
- tool invocation and callback delivery;
- licence verification;
- clock, identifier, and cost-meter sources when deterministic testing requires them;
- Softwaretest.it reporting outside the product runtime graph.

Ports are defined by the consuming application module. Adapters translate external data into canonical contracts.

Prohibited:

- An interface for every class.
- Wrapping stable library functions without a volatility or testing reason.
- Provider SDK types in domain or application signatures.
- One universal integration interface that erases materially different semantics.

Verification:

ARCH-001, ARCH-003, ARCH-010, and ARCH-011; provider contract tests; import dependency checks.

## ADR-003 — Application Service and explicit Use Case pattern

Status: PROPOSED

### Context and decision

HTTP handlers, scheduled jobs, worker activities, and administrative commands must not duplicate authorisation, transaction, validation, and audit behaviour.

Each externally triggered business operation is an application use case. Transport adapters authenticate and parse, then call the use case with canonical commands and verified context. The use case coordinates domain objects, policies, repositories, ports, transaction boundaries, and audit emission.

Representative use cases:

- CreateProject
- ConfigureEndpoint
- SynchroniseKnowledgeSource
- ValidateWorkflowDraft
- PublishWorkflow
- StartRun
- CancelRun
- DecideHumanTask
- DeleteProject

Prohibited:

- Business decisions in FastAPI routes, Next.js server actions, queue consumers, or durable-engine wrappers.
- A generic execute-any-command dispatcher without explicit contracts.

Verification:

ARCH-002; route and worker dependency tests; focused use-case tests without framework startup.

## ADR-004 — Aggregate Repository plus Unit of Work, not generic CRUD repositories

Status: PROPOSED

### Context and decision

Some operations preserve invariants across several persisted records. A generic repository per table would hide query cost and spread invariants.

Use repositories only for aggregate roots:

- Project
- KnowledgeSource
- WorkflowDraft
- PublishedWorkflow
- AgentVersion
- Run
- HumanTask
- PolicyVersion
- LicenceGrant

Use a Unit of Work per command use case for PostgreSQL transactions. List and reporting queries use explicit query services or projections.

Prohibited:

- A shared GenericRepository type.
- ORM entities crossing module boundaries.
- A transaction spanning model, connector, tool, callback, or other external calls.

Verification:

Transaction integration tests, module-boundary tests, and failure injection around commit and external hand-off.

## ADR-005 — Persisted State Machine for lifecycle-heavy entities

Status: PROPOSED

### Context and decision

Runs, node attempts, human tasks, synchronisation jobs, publication, and callbacks have invalid transitions, timeouts, retries, and terminal outcomes.

Use explicit persisted state machines for:

- Run
- NodeAttempt
- HumanTask
- KnowledgeSync
- CallbackDelivery
- WorkflowPublication

Transitions validate current state, command, identity, policy version, and optimistic-lock version. Every accepted transition emits an attributable audit event.

Prohibited:

- Arbitrary string status updates.
- Inferring authoritative state from logs.
- Moving a timed-out human task to approved.
- Reopening immutable publication.

Verification:

Transition-table tests, invalid-transition property tests, optimistic-concurrency tests, restart tests, and timeout tests.

## ADR-006 — Durable Saga and Process Manager for workflow runs

Status: PROPOSED at pattern level; engine selection remains BLOCKING

### Context and decision

Workflow runs span model calls, connectors, tools, approvals, timers, retries, callbacks, and process restarts. A database transaction cannot cover them.

Model each run as a durable process manager implemented through the selected durable execution engine. It owns orchestration, checkpoints, timers, retry decisions, cancellation, and explicit compensation commands.

The workflow graph is execution data interpreted by a versioned runtime. Side effects remain in activities or adapters and are protected by idempotency or compensation.

Prohibited:

- In-memory orchestration in an API process.
- Distributed two-phase commit across external systems.
- Automatic compensation without an explicitly defined safe inverse.
- Building a bespoke durable engine.

ADR-PENDING-001 must select the engine based on offline deployment, PostgreSQL support, licensing, worker model, pause and resume, cancellation, visibility, recovery, and operations.

Verification:

ARCH-008 and ARCH-009; worker-loss, restart, duplicate-delivery, cancellation, approval-resume, and uncertain-response tests.

## ADR-007 — Transactional Outbox for committed dispatch intent

Status: PROPOSED

### Context and decision

A database commit and event publication or callback scheduling cannot be atomic across separate systems.

Write event or dispatch intent to an outbox in the same PostgreSQL transaction as the owning state change. A dispatcher claims, delivers, and records attempts idempotently.

Use it for:

- audit hand-off when separate processing is required;
- callback delivery intent;
- durable-engine start or signal hand-off when the engine cannot share the transaction;
- connector or indexing follow-up work where loss breaks consistency;
- later notification and reporting events.

Prohibited:

- Treating the outbox as the full product event store.
- Publishing every in-process notification through PostgreSQL.
- Removing failed attempts before retention allows it.

Verification:

Commit-crash-window tests, duplicate dispatcher tests, retry visibility, and reconciliation.

## ADR-008 — Idempotent Consumer and Inbox at repeatable boundaries

Status: PROPOSED

### Context and decision

HTTP retries, event sources, durable redelivery, connector cursors, and client timeouts create duplicate messages or uncertain outcomes.

Use stable idempotency identities and a durable inbox or equivalent record at:

- Process API run start;
- human-task decisions;
- event-triggered run starts;
- durable commands with external side effects;
- consumed webhooks or events;
- connector item ingestion with stable source identity.

The record stores request fingerprint, result reference, status, project scope, and bounded retention. Conflicting reuse is rejected.

Prohibited:

- Treating timeout as proof that no operation occurred.
- In-memory-only deduplication.
- Reusing keys across projects or operation types.

Verification:

Concurrent duplicate, conflicting-payload, crash-retry, and cross-project tests.

## ADR-009 — Strategy plus Adapter for provider and connector variants

Status: PROPOSED

### Context and decision

The product supports multiple providers and connector types with shared orchestration but different capabilities and failure semantics.

Use:

- an Adapter per provider or connector implementation;
- a Strategy selected by versioned configuration;
- a capability descriptor for supported operations, streaming, structured output, authentication, limits, and retry safety;
- an explicit registry in the composition root mapping stable type and version identifiers to implementations.

Examples:

- OpenAIAdapter and OpenAICompatibleAdapter implement ModelExecutionPort but have separate compatibility suites.
- QdrantVectorStoreAdapter implements VectorStorePort.
- FileConnector, RestConnector, and GitConnector implement ConnectorPort.
- Tool handlers implement typed ToolPort contracts.

Prohibited:

- Runtime reflection or user-supplied module names.
- Provider conditionals spread through use cases.
- Assuming OpenAI-compatible means semantically identical.
- Untrusted third-party connector code in 0.1.

Verification:

Adapter compliance suites, capability negotiation, registry allowlist, and provider-specific negative tests.

## ADR-010 — Anti-Corruption Layer for provider semantics

Status: PROPOSED

### Context and decision

Providers differ in response types, token usage, errors, tool calls, rate limits, and streaming.

Each provider adapter maps:

- canonical commands to provider requests;
- provider responses to canonical results;
- native errors to stable error categories;
- usage to canonical usage and cost records;
- provider identifiers to opaque external references.

Raw provider payload retention is opt-in and governed by data policy.

Prohibited:

- Branching on provider error strings in application logic.
- Persisting SDK objects as domain state.
- Leaking provider-specific fields into the stable Process API without versioning.

Verification:

Golden contract fixtures, unknown-field tolerance, error mapping, and secret-redaction tests.

## ADR-011 — Versioned Policy Object for governance decisions

Status: PROPOSED

### Context and decision

Approval, network, citation, limit, retention, and evaluation decisions vary by project, workflow, agent, and installation.

Represent them as immutable versioned policy objects evaluated by side-effect-free policy services:

- WriteApprovalPolicy
- NetworkEgressPolicy
- CitationPolicy
- RunLimitPolicy
- PayloadRetentionPolicy
- EvaluationGatePolicy

Evaluation returns a typed decision such as allow, deny, require approval, warn, or stop, plus a safe reason and policy version.

Prohibited:

- Tool or network activity during policy evaluation.
- A global bypass flag.
- Mutating a policy version referenced by publication or run.
- Treating model output as policy authority.

Verification:

Decision-table, precedence, version-binding, deny-by-default, and audit-correlation tests.

## ADR-012 — Handler Registry and Factory for workflow node types

Status: PROPOSED

### Context and decision

The runtime needs controlled node extensibility without a growing conditional chain or arbitrary code loading.

Each node type has:

- a stable type identifier and schema version;
- a validator and typed configuration;
- a runtime NodeHandler;
- declared input, output, retry, side-effect, and policy characteristics.

A registry assembled in the worker composition root resolves handlers. A factory constructs them with approved ports and execution context.

Prohibited:

- User-supplied class or module names.
- A service locator available to domain code.
- Unrestricted network or secret access from handlers.
- Silent reinterpretation of a schema version.

Verification:

Registry uniqueness, unknown-type rejection, compatibility, capability declaration, and dependency tests.

## ADR-013 — Schema-first canonical contracts and boundary mappers

Status: PROPOSED

### Context and decision

Visual editing, YAML or JSON, APIs, events, callbacks, connector SDKs, and snapshots need one meaning across TypeScript and Python.

Define versioned schemas in `contracts`. Generate or validate boundary types for both languages. Translate DTOs to domain commands and values at adapters.

The workflow schema is the only semantic source for both editors. Published snapshots store schema version and content digest.

Prohibited:

- ORM entities as API contracts.
- Separate visual and runtime workflow models.
- Breaking a published schema in place.

Verification:

ARCH-006 and ARCH-012; round-trip, compatibility, cross-language fixture, and unknown-version tests.

## ADR-014 — Optimistic concurrency for mutable administration

Status: PROPOSED

### Context and decision

Drafts, connector settings, policies, endpoints, and knowledge settings can be edited concurrently.

Use version fields or entity tags. Updates include the observed version. Stale updates return a conflict. Publication takes a consistent snapshot from one accepted version. Database uniqueness and conditional writes protect idempotency, publication numbering, and bootstrap.

Prohibited:

- Last-write-wins for workflow drafts or security policy.
- Database locks held across user interaction or external calls.

Verification:

Concurrent-update, stale-version, bootstrap-race, and publication-consistency tests.

## ADR-015 — Command and Query Separation without global CQRS

Status: PROPOSED

### Context and decision

Run traces, dashboards, lists, and audit searches need efficient read shapes. A full CQRS platform with separate databases would add consistency and operations complexity.

Separate command use cases from query services at the application interface. Permit views or denormalised read models for measured high-volume run and audit queries. Use the same PostgreSQL source of truth in 0.x. Read models are rebuildable and never authoritative for commands.

Prohibited:

- A mandatory command or query bus for simple in-process calls.
- Separate read and write databases without a scaling ADR.
- Updating domain state through a projection.

Verification:

Dependency checks, projection rebuild tests where introduced, and stale-read tests.

## ADR-016 — No Event Sourcing for 0.x platform state

Status: PROPOSED

### Context and decision

Auditability and durable runs do not require replaying all platform state from domain events. Event-sourced schema evolution would add major complexity.

Use current-state persistence with immutable versions, append-only audit events, durable-engine history, attempts, and outbox records. These histories are evidence, not the sole source of truth for all aggregates.

Prohibited:

- Reconstructing ordinary configuration solely from audit logs.
- Claiming audit events form a complete event-sourced model.

Review trigger:

Reconsider only if a concrete capability requires temporal reconstruction that immutable versions and audit records cannot provide.

## ADR-017 — Dependency Injection through explicit composition roots

Status: PROPOSED

### Decision

Each deployable has one explicit composition root:

- `backend/src/apistra/entrypoints/api/composition.py`
- `backend/src/apistra/entrypoints/worker/composition.py`
- `apps/web/src/app/bootstrap.ts`
- `engineering/softwaretest` bootstrap when that adapter is implemented

Constructor injection is the default. Framework DI is allowed only at the outer composition boundary.

Prohibited:

- Global mutable service locators.
- Domain modules resolving adapters.
- Production branches added only to swap test dependencies.

Verification:

ARCH-011 dependency tests and composition smoke tests.

## ADR-018 — Typed Result and stable error taxonomy

Status: PROPOSED

### Context and decision

Provider, database, validation, policy, and runtime failures must be diagnosable without leaking infrastructure or sensitive data.

Application boundaries use stable error categories:

- validation
- authentication
- authorisation
- conflict
- not found
- policy denied
- limit exceeded
- retryable dependency
- permanent dependency
- cancelled
- internal

Adapters translate native exceptions. Transport maps typed outcomes to safe responses. Unexpected exceptions receive correlation and redaction.

Prohibited:

- Returning stack traces or provider payloads to clients.
- Catch-all success results.
- Retry decisions based on free-form messages.

Verification:

Error-mapping, safe-message, retry-classification, and redaction tests.

## ADR-019 — Monorepo layout and executable dependency boundaries

Status: DECIDED

Decision date: 2026-09-29

### Context and decision

Apistra needs independently understandable web, backend, public-contract, connector-SDK, deployment, and engineering boundaries without introducing multiple Python distribution graphs or a monorepo orchestrator before measured need.

Use one public monorepo with:

- `apps/web` for the TypeScript web application;
- `backend` for one installable Python package used by separate API and worker entrypoints;
- `contracts/{openapi,workflow,events,connectors}` for language-neutral canonical contracts;
- `connector-sdk/python` for the public Python connector boundary;
- `deploy/compose` for local, test, and isolated staging packaging;
- `engineering/softwaretest` for test-management integration outside the product runtime;
- `tests/architecture-fixtures` for retained positive and negative dependency graphs;
- `tools` for repository automation.

Backend business ownership is module-first. A module contains `domain`, `application`, `ports`, and `adapters`, and exposes cross-module use only through `modules.<name>.public`. Dependencies point inward: domain; application and ports; adapters; entrypoint composition roots. The API and worker share the backend package but have separate explicit composition roots.

Use uv for the Python project and pnpm workspaces for TypeScript. Do not add Nx, Turborepo, or multiple Python workspace packages until measured build or ownership pressure justifies a new ADR.

### Consequences

- Module ownership is enforceable without premature network-service boundaries.
- API and worker code cannot drift into separate domain models.
- Language-neutral contracts and the connector SDK have visible ownership.
- A single Python lock and a single pnpm lock keep clean-clone execution reproducible.
- Adding a module requires a public contract and the standard internal layer direction.

### Verification

CI-TS-03 runs Import Linter, pytest plus AST rules, Dependency Cruiser, and pnpm workspace-cycle protection. Source discovery fails closed on an empty scope. Retained allowed fixtures must pass and retained forbidden fixtures must fail. No initial exceptions exist; a future exception requires rule ID, reason, owner, expiry, removal workorder, and approval.

## Pattern-to-module summary

Cross-cutting backend:

- Modular monolith: all backend modules
- Application Service: all externally triggered use cases
- Unit of Work: PostgreSQL-backed commands
- Explicit composition root: API, worker, web bootstrap, engineering adapter
- Typed Result: application boundaries

Workflow runtime:

- Persisted State Machine: runs, attempts, human tasks, synchronisation, callbacks, publication
- Durable Saga or Process Manager: run orchestration
- Idempotent Consumer: starts, signals, decisions, and side-effect commands
- Transactional Outbox: committed dispatch intent
- Handler Registry and Factory: node execution

External integration:

- Ports and Adapters: providers, connectors, vector store, durable engine, tools, identity, licence
- Strategy: versioned implementation selection
- Anti-Corruption Layer: request, result, usage, and error translation

Governance:

- Policy Object: approvals, egress, citations, limits, retention, evaluation
- Immutable Version: workflows, agents, policies, endpoint and knowledge configuration
- Optimistic Concurrency: mutable drafts and administration

Deliberately not selected globally:

- Microservices
- generic repository for every table
- global CQRS infrastructure
- Event Sourcing
- distributed two-phase commit
- service locator
- arbitrary runtime plugin loading

## Decision gate

ADR-019 is product-owner approved and implemented as the architecture-test foundation. ADR-001 through ADR-018 remain PROPOSED until qualified architecture review. ADR-PENDING-001 for the durable engine and ADR-PENDING-004 for authentication implementation still block their dependent workorders.
