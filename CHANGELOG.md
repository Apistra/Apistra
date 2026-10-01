# Changelog

All notable changes to Apistra are documented in this file.

The format follows Keep a Changelog and the project follows Semantic Versioning as defined in `VERSIONING.md`.

## [Unreleased]

### Added

- BuildBySpec planning baseline covering product scope, decisions, arc42 architecture, security, delivery/CI, test architecture, design, traceability, and gates.
- Nineteen granular capability contracts and 140 individual workorder contracts for the 0.x roadmap.
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
- CAP-00 independent review and human bootstrap acceptance record; external reporting evidence remains separate.
- Proposed administration interaction baseline for DSN-001 through DSN-004 and six repository-authoritative, atomic `MTP-PRC-01` manual test definitions covering bootstrap, authentication, session revocation, project creation/audit, and project isolation.
- Proposed business-workorder repository path contract mapping all 133 CAP-01 through CAP-18 workorders to observed existing paths and explicitly labelled planned module, feature, contract, test, migration, staging, and evidence paths.
- Approved CAP-01 expectation, security, architecture, design, pattern, and repository-path review with the remaining external Softwaretest.it blocker preserved.
- Repository-owned BDD-AUTH-001 and BDD-PROJ-001 scenarios for CAP-01.
- Deterministic, checksummed CAP-01 fixture descriptors and fail-closed integration/contract tests without product-state mutation or embedded credentials.
- Versioned Softwaretest.it CI-guide validation, structured precondition diagnostics, revision-bound command keys, explicit run start, and an opt-in protected round-trip trigger.
- Softwaretest.it CI guide 1.1 contract validation, direct cycle-bound report publication, and structured missing-cycle remediation evidence without an inferred automation-resource prerequisite.
- Complete Softwaretest.it report batches with an explicit required-stage result and canonical UTC-millisecond timestamps for exact field-level readback.

### Changed

- Capability roadmap and workorder catalogue now act as indexes to one canonical file per capability and workorder.
- All 140 workorders now use the version 0.6 execution contract with exact workflow status, separate implementation/evidence/approval state, delivery classes, explicit outcomes, examples and counterexamples, canonical test references, workorder-specific architecture/security applicability, dependency graphs, and evidence invalidation rules.
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

- Containers run non-root with read-only filesystems, dropped capabilities, no-new-privileges, and declared resource limits.
- Runtime and evidence contracts require secret references, safe diagnostics, project isolation, bounded egress, and no hidden telemetry.

### Known limitations

- CAP-00 formal completion still requires a successful authenticated Softwaretest.it write/import/finalize/readback round-trip with all receipts bound to the final immutable candidate. Guide 1.1.0 removes the previously inferred automation-resource prerequisite. Independent review and human bootstrap acceptance were recorded on 2026-09-30.
- CAP-01 through CAP-18 are planning contracts only and are not implemented or accepted.
- No production environment or automatic deployment path exists.
