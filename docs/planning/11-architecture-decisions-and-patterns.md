# Architecture Decisions and Pattern Catalogue

Version: 0.4-draft
Status: DRAFT; CAP-01 PATTERN SLICE APPROVED
Assurance profile: EXTENDED

This document makes the software-architecture choices operational. Pattern names are not quality claims. Every decision states the concrete problem, scope, simpler alternative, intended use, prohibited use, consequences, and verification.

## ADR-001 — Modular monolith as the 0.x backend system style

Status: PROPOSED

CAP-01 applicability: DECIDED on 2026-09-30

### Context and decision

Apistra has substantial domain boundaries but begins with one product team, one installation model, and a Docker Compose deployment. Independent microservices would add distributed transactions and operational failure modes before independent scaling or ownership requires them.

Use a modular monolith for backend source and domain ownership, deployed through separate API and worker processes from the same versioned backend codebase. The Next.js web application is separate. PostgreSQL is physically shared in 0.x, while each module owns its schema or tables and exposes application contracts.

Modules:

- identity
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

Model providers, embedding providers, vector stores, connectors, identity systems, licences, clocks, identifiers, and external tools can vary or introduce vendor-specific semantics. Durable orchestration is an owned Apistra capability and is not delegated to a third-party product.

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

CAP-01 applicability: DECIDED on 2026-09-30

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

CAP-01 decision:

The Project is the aggregate root and uses a project repository plus one unit
of work per command. Race-safe Administrator bootstrap uses the same bounded
transaction rule through dedicated `AdministratorStore` and `SessionStore`
ports owned by the `identity` module. Administrator and session persistence do
not introduce a generic repository or cross-module ORM relationship.

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

## ADR-006 — Apistra-owned durable Saga and Process Manager

Status: PROPOSED at pattern level; product ownership is decided by ADR-020

### Context and decision

Workflow runs span model calls, connectors, tools, approvals, timers, retries, callbacks, and process restarts. A database transaction cannot cover them.

Model each run as a durable process manager implemented by the Apistra runtime. It owns orchestration, checkpoints, timers, retry decisions, cancellation, and explicit compensation commands. PostgreSQL is the durable system of record; API and worker processes remain replaceable execution hosts.

The workflow graph is execution data interpreted by a versioned runtime. Side effects remain in activities or adapters and are protected by idempotency or compensation.

The owned runtime is split into persisted state machines, an append-only execution journal, transactional outbox and inbox records, lease-based dispatch, idempotency records, durable timers, human-signal intake, and explicit recovery operations. Current state remains directly queryable; the journal does not introduce global Event Sourcing.

Prohibited:

- In-memory orchestration in an API process.
- Distributed two-phase commit across external systems.
- Automatic compensation without an explicitly defined safe inverse.
- A runtime dependency on an external workflow engine, hosted control plane, online licence service, or paid management product.
- Embedding orchestration semantics in a replaceable library or adapter.

Runtime delivery is incremental: durable sequential execution; graph decisions and fan-out/fan-in; human waits and signals; operational pause, resume, cancellation, and diagnosis; compensation and uncertain-response recovery; then measured scale, priority, and fairness. Each slice must pass crash, duplicate-delivery, stale-lease, version-compatibility, and recovery tests before later slices rely on it.

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

CAP-01 applicability: DECIDED for mutable project administration on 2026-09-30

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

## ADR-020 — Apistra-owned durable execution runtime

Status: DECIDED

Decision date: 2026-09-30

### Context and decision

Durable orchestration is part of Apistra's differentiating product capability. Depending on an external workflow product or its control plane would make offline operation, commercial continuity, and core behaviour subject to another provider's pricing, roadmap, availability, and licence decisions.

Apistra therefore owns the execution state model, scheduler and dispatcher semantics, worker protocol, timer and signal handling, idempotency and recovery rules, operational inspection model, and compatibility contract. PostgreSQL provides durable storage and concurrency primitives but does not own product semantics.

Third-party libraries may implement generic technical mechanisms only when they are offline-capable, licence-compatible, pinned, inventoried, isolated behind an owned boundary, and practically replaceable or forkable. No external orchestration server, SaaS, control plane, licence service, or paid feature is required to start, execute, recover, inspect, or administer a run.

### Consequences and verification

- CAP-06 owns the first vertically usable durable runtime rather than integrating an external engine.
- CAP-07 adds durable human interaction; CAP-08 adds advanced graph control without replacing the runtime core.
- ARCH-008 and ARCH-009 remain mandatory; a new dependency rule rejects imports or deployment dependencies on third-party orchestration products.
- Worker-loss, restart, duplicate delivery, lease expiry, stale result, cancellation, approval resume, timer recovery, version evolution, backup/restore, and uncertain external response are mandatory test classes.
- Runtime scope grows only through accepted capability slices; a general-purpose BPM platform is not implied.

## ADR-021 — Local Administrator authentication

Status: DECIDED

Decision date: 2026-09-30

Release 0.1 uses local Administrator authentication suitable for offline installation. Passwords use Argon2id through an established library. Browser authentication uses opaque, revocable server-side sessions stored in PostgreSQL and secure, HTTP-only, same-site cookies with server-side CSRF protection. Bootstrap and recovery are local privileged CLI operations with no default credential, email, hosted identity, or phone-home dependency. Session rotation, timeout, revocation, and security events are explicit and testable. OIDC and enterprise identity remain CAP-15 concerns.

## ADR-022 — Source-available and commercial licensing boundary

Status: DECIDED; IMPLEMENTED

Decision date: 2026-09-30

Releases from the transition commit are source available under PolyForm Noncommercial 1.0.0 for its permitted purposes, with PolyForm Free Trial 1.0.0 as the company-evaluation path for fewer than 32 consecutive calendar days. Productive commercial use, internal business operation, commercial integration, redistribution, resale, SaaS, and managed-service operation require a separate licence signed by the licensee and Jens Bekersch.

Apistra must not be described as OSI Open Source under this model. Existing AGPL grants remain valid for versions already published. `LICENSE-TRANSITION.md` identifies the last AGPL commit and the first source-available commit; `NOTICE` supplies the Required Notice; `COMMERCIAL-LICENSE.md` contains the standard commercial terms. External contributions remain closed until an explicit compatible rights grant is introduced. No mandatory online activation is introduced.

## ADR-023 — Multiple local principals and guarded acceptance fixtures

Status: DECIDED

Decision date: 2026-10-01

### Context and decision

Project isolation must be proven against an existing foreign project, but a
single-row identity schema cannot represent that state and would prevent later
role assignment. One installation may therefore persist multiple local
principals. This is a persistence capability, not an early user-management
feature: release 0.1 still exposes only the bootstrap Administrator role.

Bootstrap no longer relies on a unique installation column. The PostgreSQL
adapter takes a transaction-scoped advisory lock, checks for an existing
login-enabled local principal, and creates the first Administrator, session,
and audit event atomically. Concurrent attempts therefore produce one success
and one safe closed-bootstrap result. Usernames remain unique.

CAP-01 acceptance uses a separate process entrypoint to reset an ephemeral
local-staging database and create deterministic Atlas and Orion ownership. Its
foreign owner is explicitly non-login-enabled and receives no usable
credential. The process is absent from the HTTP API and requires all of these
conditions before connecting to PostgreSQL:

- exact `local-staging-<run-id>` environment identity;
- matching `apply-cap01-<run-id>` fixture gate;
- exact named-fixture reset confirmation;
- explicit Compose `fixtures` profile;
- protected password injection for login-enabled fixtures.

### Consequences and verification

- Project queries remain owner-scoped and foreign/unknown responses remain
  indistinguishable.
- A disabled fixture principal cannot authenticate even if its username is
  known.
- Migration, competing-bootstrap, reset idempotency, disabled-login,
  Atlas-listing, and Orion-denial tests are mandatory.
- Fixture execution emits a secret-free candidate/run/revision/checksum/count
  receipt and is never a production deployment action.
- Additional roles, invitations, recovery, and user administration remain
  separately gated capabilities.

## ADR-024 — Google/PEP-based executable Python convention profile

Status: DECIDED

Decision date: 2026-10-01

### Context and decision

Apistra needs one readable Python contract before more product code is added. The
repository adopts the Google Python Style Guide and PEP 8/257 as its baseline,
then narrows them through the binding Apistra profile in
`docs/engineering/python-code-conventions.md`. The repository profile wins where
the upstream guides allow alternatives.

The contract is executable. Ruff owns formatting, imports, common correctness,
modernisation, security-oriented static checks, annotations, and complexity.
Mypy checks product code in strict mode. The pinned wemake-python-styleguide
rules `WPS226` and `WPS432` reject overused string literals and unexplained
non-trivial numbers in product and repository-owned engineering code. CI also
rejects blanket suppression directives.

Constants are required for stable domain vocabulary, protocol and persistence
discriminators, security parameters, thresholds, timeouts, limits, and strings
used more than three times in one module. This is not a rule that every literal
must become a constant: obvious local values, one-use diagnostics, test data,
docstrings, comments, and typed configuration stay close to their use.

### Consequences and verification

- Python tooling versions are lockfile-pinned and updated through reviewed dependency changes.
- Test scenarios favour visible values, while product and repository-owned engineering code use named policy vocabulary.
- New violations fail CI-TS-18; there is no grandfathering and no blanket local bypass.
- Retained positive and negative fixtures prove that the convention gate can both accept and reject.
- Architecture and code review remain responsible for semantics that static analysis cannot infer.

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

- Ports and Adapters: providers, connectors, vector store, worker execution mechanisms, tools, identity, licence
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

ADR-019 is product-owner approved and implemented as the architecture-test foundation. ADR-020 through ADR-023 are product-owner approved constraints, and ADR-022 is implemented by the repository licence set and transition record. ADR-001 through ADR-018 remain PROPOSED globally until qualified architecture review.

The CAP-01 slice is approved by the readiness review dated 2026-09-30:
ADR-001 through ADR-004 where explicitly mapped, ADR-013, ADR-014 for mutable
project administration, ADR-017, and ADR-018. ADR-002 covers identity/session
and Softwaretest.it boundaries; ADR-010 applies only to the Softwaretest.it
adapter. ADR-005 is explicitly not applicable to CAP-01. ADR-019 and ADR-021
and ADR-023 remain the decided layout, authentication, principal, and guarded
acceptance-fixture constraints. This scoped decision
does not approve those proposed ADRs for unrelated capabilities.
