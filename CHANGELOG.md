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
- Synthetic CAP-00 engineering fixtures and secret-detection proof fixture.
- AGPLv3 licence, commercial-licence notice, contribution policy, security policy, issue templates, pull-request template, CODEOWNERS, and expected branch-protection contract.
- System-centred test architecture and operational test concept.
- Repository-wide Semantic Versioning policy and central `VERSION` authority.

### Changed

- Capability roadmap and workorder catalogue now act as indexes to one canonical file per capability and workorder.
- Repository contract validation now checks the complete planning catalogue, required sections, IDs, membership, and local links.

### Security

- Containers run non-root with read-only filesystems, dropped capabilities, no-new-privileges, and declared resource limits.
- Runtime and evidence contracts require secret references, safe diagnostics, project isolation, bounded egress, and no hidden telemetry.

### Known limitations

- CAP-00 formal acceptance still requires live branch protection, an authenticated Softwaretest.it write/read round-trip, independent review, and human bootstrap acceptance.
- CAP-01 through CAP-18 are planning contracts only and are not implemented or accepted.
- No production environment or automatic deployment path exists.
