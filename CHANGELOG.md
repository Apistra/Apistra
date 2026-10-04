# Changelog

All notable changes to Apistra are documented in this file.

The format follows Keep a Changelog and the project follows Semantic Versioning as defined in `VERSIONING.md`.

## [Unreleased]

- Advanced WO-CAP-02-03 to source revision `0.10-ready` after its implementation-state update and documented the mandatory monotonic Steering version rule; safe CI errors now expose the redacted HTTP code, phase, batch, and request ID so `REVISION_CONTENT_CONFLICT` is actionable without downloading an artifact.
- Implemented WO-CAP-02-03 on its feature branch with immutable project-scoped agent versions, exact primary and optional fallback endpoint-version bindings, explicit-only routing order, append-only draft creation, idempotency and conflict handling, safe audit events, PostgreSQL migration/persistence, versioned OpenAPI, DSN-022, architecture contracts, and automated backend/web verification; protected CI, independent implementation review, merge, and human approval remain pending.
- Completed WO-CAP-02-02 after PR #33, protected merge `96dfa5e`, green run 37228142970, authenticated Steering/definition/receipt readback, and product-owner merge approval; WO-CAP-02-03 is now READY without implying CAP-02 acceptance or production approval.
- Implemented WO-CAP-02-02 on its feature branch with project-scoped generative and embedding endpoint definitions, offline idempotent save, optimistic probe versioning, credential-safe deny-by-default egress and DNS-rebinding controls, pinned read-only OpenAI-compatible model discovery, normalized safe outcomes, PostgreSQL persistence/migration, versioned OpenAPI, audit events, and DSN-005; protected CI, independent review, merge, and human approval remain pending.
- Completed WO-CAP-02-01 after PR #31, protected merge `dfa8319`, green run 37216514042, authenticated Steering/definition/receipt readback, and explicit product-owner implementation approval; WO-CAP-02-02 is now READY without implying CAP-02 acceptance or production approval.
- Added the WO-CAP-02-01 encrypted project secret-reference slice with AES-256-GCM envelopes, operator-file key configuration, opaque versioned APIs, project isolation, idempotency, safe audit evidence, PostgreSQL migration, DSN-006 administration UI, and executable architecture/security/contract tests.
- Closed WO-CAP-02-06 from protected run 37212285531 after authenticated publication and exact readback of all CAP-02 test definitions.
- Approved the CAP-02 design and independent expectation/architecture/security review, added five stable BDD scenarios, eight atomic manual definitions, deterministic secret-free fixture descriptors, package-aware Softwaretest.it publication with exact ordered-step readback, and the protected CI handover required by WO-CAP-02-06.
- Prepared the reviewable CAP-02 architecture, security, repository-path, design, traceability, and workorder baseline for project-scoped secrets, model endpoints, immutable agent versions, tools, and limits. Added ADR-024/ADR-025, DSN-022/DSN-023, reserved automated and manual test identities, taught repository validation to distinguish reserved cases from allocated definitions, and kept product implementation blocked behind design approval, independent review, and verified test publication/read-back.
- Aligned the fail-closed Softwaretest.it Steering integration with Guide 1.3.0: new imports use RFC 8785/JCS SHA-256 receipts, validate the declared hash contract and exact digest, rotate to the `steering.import.v2` idempotency namespace, and retain guarded replay compatibility for legacy receipts.
- Marked the accepted CAP-01 source transmission as published from protected run 37199065456 so the derived Steering view reports `CONFIRMED` instead of `UNKNOWN`.
- Accepted CAP-01 and completed WO-CAP-01-05 from the exact local-staging fix candidate, tree-equivalent protected `test` merge, green CI run 37192774502, successful direct defect retests, authenticated closure of all linked defects, and explicit product-owner approval. The unused `NOT_STARTED` repeat remains documented as a Softwaretest.it reporting exception rather than being rewritten.
- Compare Softwaretest.it Steering read-back timestamps as timezone-aware RFC 3339 instants while retaining strict comparison for every non-temporal field.

- Split the CI quality matrix into explicit executable stages and limited CI-TS-12 to deterministic resource and boundary-load contracts until representative performance infrastructure exists.
- Published all six CAP-01 manual definitions to Softwaretest.it with exact field-/ordered-step read-back, stable source/payload fingerprints, zero-result separation, and an idempotent protected-CI publisher.

### Changed

- Refactored API route composition, Softwaretest.it parsing/reporting, architecture analysis, repository-contract validation, and immutable-candidate verification into smaller single-purpose functions without changing their external contracts.
- Adopted the Google/PEP-based Apistra Python convention profile and refactored existing product and engineering code to use typed boundaries and named domain, protocol, security, timeout, and limit constants.

### Added

- A separate fail-closed CI-TS-19 Softwaretest.it Steering publisher for all 19 capabilities and 141 workorders, with stable source revisions, payload-bound idempotency, redacted receipts, and complete export field readback.

- A fail-closed CI-TS-18 Python convention gate with strict product-code type checking, expanded Ruff checks, selected repeated-string and magic-number rules, blanket-suppression detection, and retained positive and negative proof fixtures.
- A fail-closed CI-TS-17 cyclomatic-complexity gate with a hard maximum of 10 for Python and TypeScript/TSX/JavaScript, including retained positive and negative analyser fixtures.
- Guarded CAP-01 local-staging fixture application with deterministic Atlas and
  Orion ownership, disabled foreign login, secret-free application receipts,
  and explicit environment/run/reset gates outside the product HTTP API.
- CAP-01 administration views for bootstrap status, Administrator actions,
  expired-session guidance, exact approved page titles, and rendered
  installation/project audit identifiers.
- Authenticated CAP-01 audit read model with Administrator- and project-owner scoping, exact approved event labels, safe direct project routes, an audit-log route, and immutable staging verification of revocation attribution.
- CAP-01 isolated project lifecycle with owner-scoped PostgreSQL persistence, idempotent creation,
  optimistic version checks, safe foreign/unknown-project handling, attributable project audit
  events, a versioned administration API contract, and the approved sign-in/project UI flow.
- Immutable staging verification of project create, list, update, archive, session revocation, and
  unchanged-image recovery through the same-origin web boundary.
- CAP-01 local Administrator bootstrap with Argon2id credentials, opaque revocable sessions,
  server-side CSRF verification, safe audit events, PostgreSQL persistence/migration, a versioned
  HTTP contract, and the approved dark first-run administration interface.
- Digest-pinned PostgreSQL and an idempotent migration gate in isolated candidate staging, plus
  real PostgreSQL integration coverage in CI.
- BuildBySpec planning baseline covering product scope, decisions, arc42 architecture, security, delivery/CI, test architecture, design, traceability, and gates.
- Nineteen granular capability contracts and 141 individual workorder contracts for the 0.x roadmap.
- Architecture decision and pattern catalogue with executable Python and TypeScript boundary tests and retained negative fixtures.
- CAP-00 health-only web, API, and worker walking skeleton.
- Immutable container-candidate builder with manifest, checksums, dependency inventory, and SPDX SBOM.
- Isolated manual local-staging verification with health, deployment markers, controlled failure, and unchanged-image recovery.
- GitHub Actions gates for contracts/static checks, architecture, tests, security/supply chain, and candidate packaging.
- Public Softwaretest.it OpenAPI preflight, result-bundle contract, dry-run publisher, lossless outbox, and adapter tests.
- Protected GitHub `softwaretest` environment, trusted-branch reporting job, authenticated reporting preflight, cycle resolution, field-level report readback, and redacted atomic receipt support.
- Synthetic CAP-00 engineering fixtures and secret-detection proof fixture.
- AGPLv3 licence, commercial-licence notice, contribution policy, security policy, issue templates, pull-request template, CODEOWNERS, and expected branch-protection contract.
- System-centred test architecture and operational test concept.
- Repository-wide Semantic Versioning policy and central `VERSION` authority.
- Canonical semantic behavioural test-ID and process-level manual package catalogue.
- ARCH-015 for explicit, versioned, fail-closed policy decisions.
- Product-owner decisions ADR-020 through ADR-022 for the Apistra-owned durable runtime, local Administrator authentication, and the implemented source-available licensing boundary.
- Source-available licence set with PolyForm Noncommercial 1.0.0, PolyForm Free Trial 1.0.0, standard commercial terms, Required Notice, and an explicit historical AGPL boundary.
- CAP-00 independent review and human bootstrap acceptance record with external reporting retained as a separate evidence dimension.
- Proposed administration interaction baseline for DSN-001 through DSN-004 and six repository-authoritative, atomic `MTP-PRC-01` manual test definitions covering bootstrap, authentication, session revocation, project creation/audit, and project isolation.
- Proposed business-workorder repository path contract mapping all 133 CAP-01 through CAP-18 workorders to observed existing paths and explicitly labelled planned module, feature, contract, test, migration, staging, and evidence paths.
- Approved CAP-01 expectation, security, architecture, design, pattern, and repository-path review with the remaining external Softwaretest.it blocker preserved.
- Repository-owned BDD-AUTH-001 and BDD-PROJ-001 scenarios for CAP-01.
- Deterministic, checksummed CAP-01 fixture descriptors and fail-closed integration/contract tests without product-state mutation or embedded credentials.
- Versioned Softwaretest.it CI-guide validation, structured precondition diagnostics, revision-bound command keys, explicit run start, and an opt-in protected round-trip trigger.
- Softwaretest.it CI guide 1.1 contract validation, direct cycle-bound report publication, and structured missing-cycle remediation evidence without an inferred automation-resource prerequisite.
- Complete Softwaretest.it report batches with an explicit required-stage result and canonical UTC-millisecond timestamps for exact field-level readback.
- Verified the protected Softwaretest.it create/import/finalize/readback flow with one stage, sixteen tests, and three confirmed command receipts against the immutable `test` candidate.

### Fixed

- Made the ephemeral staging key ring readable by the deliberately unprivileged API container while retaining an owner-only host directory and a read-only mount, and preserved container diagnostics when candidate startup fails.
- Advanced the WO-CAP-02-06 numeric source revision after its reviewed content changed, resolving the protected Steering import's correctly reported same-revision content conflict.
- Fixed CAP-01 loopback acceptance sessions so browser-managed cookies work over the explicitly local HTTP boundary, project mutations retain their matching CSRF context, sign-out cannot report success before server revocation, and a previously authenticated visitor receives the required one-time expired-session guidance.
- Closed WO-CAP-00-08 from the verified trusted-branch Steering receipts and product-owner approval, and added strict source-authored criterion evidence so completed CAP-00 gates render as passed without making future criteria prematurely due.
- Corrected the Softwaretest.it Steering projection so explanatory blocker text cannot activate draft capabilities, completed item reviews remain distinct from later capability/production gates, criterion success is never inferred from item implementation, future criteria are not marked due without an explicit criterion-level due gate, and mapping changes advance source revisions monotonically.
- Aligned the fail-closed Softwaretest.it preflight with Guide 1.2.0 and its Steering/OpenAPI limits, enums, scopes, operations, and recovery contract.
- Reconciled Steering receipts across accepted and historical items, retained rejected remote receipts, and stopped guessing the undocumented server-checksum preimage while preserving exact complete-export verification.
- Corrected Steering evidence-state mapping to the running API's `MISSING`, `PARTIAL`, `CURRENT`, `FAILED`, `STALE`, and `UNKNOWN` domain instead of the unrelated file-scan enum exposed by the current OpenAPI component-name collision.
- Split Softwaretest.it Steering publication into deterministic imports of at most 100 items while preserving independent idempotency, per-batch receipts, and one complete export readback.

### Changed

- Local identity persistence now supports multiple principals while preserving
  exactly-once bootstrap through a transaction-scoped PostgreSQL advisory lock.
- Workorder validation now supports controlled 0.x DRAFT, READY, and DONE revisions while requiring
  the specification binding to match, with retained negative status and path fixtures.
- Capability roadmap and workorder catalogue now act as indexes to one canonical file per capability and workorder.
- All 141 workorders use the version 0.6 execution contract with exact workflow status, separate implementation/evidence/approval state, delivery classes, explicit outcomes, examples and counterexamples, canonical test references, workorder-specific architecture/security applicability, dependency graphs, and evidence invalidation rules; version 0.7 adds the separate Steering publication gate.
- Repository contract validation now checks the complete planning catalogue, exact status fields, canonical test IDs, defined ARCH/SEC references, dependency existence and cycles, delivery-class ordering, READY/DONE preconditions, membership, local links, and obsolete generic boilerplate.
- Repository contract validation now also proves allocated manual-case file identity, required sections, consecutive atomic steps, per-step data/oracles, logged-out entry, and a retained failing counterexample.
- Repository contract validation now rejects business-workorder path placeholders, unsafe or missing observed paths, path entries outside approved roots, and missing CAP-16/CAP-17 new-root architecture blockers; a retained failing path fixture proves the check is active.
- CAP-00 result bundles now identify the concrete GitHub run and attempt so external reporting retries remain traceable.

### Fixed

- Applied Ruff-compatible formatting to the repository contract validator.
- Removed generated `BDD-CAP-*`, `BDD-WO-*`, and `MT-CAP-*` aliases from workorders and reconciled process mappings with the canonical catalogue.
- Reconciled the control overview with successful GitHub Actions run 36637376129 while keeping version 0.6 evidence explicitly local until hosted validation.
- Enabled solo-maintainer-safe live branch protection on `test`, `staging`, and `main`, including strict required checks and administrator enforcement.

### Security

- Added real foreign-project isolation coverage against a non-login synthetic
  owner and a fail-closed fixture entrypoint that refuses non-local-staging
  targets before opening a database connection.
- Containers run non-root with read-only filesystems, dropped capabilities, no-new-privileges, and declared resource limits.
- Runtime and evidence contracts require secret references, safe diagnostics, project isolation, bounded egress, and no hidden telemetry.

### Known limitations

- Softwaretest.it currently projects direct defect retests separately from the normal repeat-run path; CAP-01 therefore retains one unused `NOT_STARTED` APISTRA-TC-000006 repeat while all linked defects are CLOSED/FIXED and the product owner has accepted the direct-retest evidence.
- CAP-02 through CAP-18 remain planning contracts only.
- No production environment or automatic deployment path exists.
