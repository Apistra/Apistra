# Versioning Policy

Version: 1.0
Status: ACTIVE FOR DEVELOPMENT

## Product version

Apistra uses Semantic Versioning 2.0.0 for the product line:

- `MAJOR.MINOR.PATCH`
- optional prerelease: `-alpha.N`, `-beta.N`, or `-rc.N`
- optional build metadata on immutable candidates: `+<commit-prefix>`

The root `VERSION` file is the authoritative base product version. Backend and web package versions must match it. The candidate builder adds the source-commit prefix as build metadata without changing the base version.

Current version: `0.0.0`. This identifies the unreleased CAP-00 development baseline and is not a public product release.

## Meaning during 0.x

- `0.Y.0`: accepted milestone release containing the named release slice.
- `0.Y.Z`: backward-compatible fixes or bounded improvements to that 0.Y line.
- `0.Y.Z-rc.N`: immutable release candidate awaiting the remaining release gates.
- `0.Y.Z-alpha.N` or `0.Y.Z-beta.N`: explicitly unstable public preview where used.

Before 1.0, a MINOR release may contain breaking changes, but every break requires explicit changelog notice, migration/compatibility guidance, and approval through the affected contract and release gates. PATCH releases must remain backward-compatible within their supported 0.Y line.

## Version authorities

- Product version: `VERSION`
- Backend distribution: `backend/pyproject.toml`
- Web package: `apps/web/package.json`
- Immutable candidate: base version plus commit metadata in the candidate manifest and runtime deployment marker
- Git release: signed or otherwise repository-approved tag `vMAJOR.MINOR.PATCH[-PRERELEASE]`
- Changelog: `CHANGELOG.md`

CI rejects a mismatch between the root, backend, and web base versions.

## Independent contract versions

Product version does not replace interface-specific versions:

- HTTP APIs and OpenAPI documents retain explicit API versions and compatibility rules.
- Workflow, event, connector, callback, result-bundle, import/export, plugin, and licence schemas retain their own schema versions.
- Published workflows, agents, policies, endpoints, knowledge configurations, datasets, and other domain objects use immutable object versions defined by their capability contract.
- Database migrations remain ordered and immutable after release.
- Planning, architecture, security, design, test, capability, and workorder documents retain their own revision headers.

A product release records the exact set of these versions; it does not force them to equal the product version.

## Compatibility rules

- Additive compatible contract changes may remain within the current contract major version.
- Breaking contract changes require a new contract major/versioned route or an explicitly approved 0.x migration window.
- Unknown required schema versions fail safely; they are never guessed or silently downgraded.
- Published immutable definitions and historical evidence remain readable for the documented support window.
- Migration, rollback/roll-forward, and import/export compatibility are tested from every supported predecessor.

## Changelog policy

`CHANGELOG.md` follows Keep a Changelog categories where applicable: Added, Changed, Deprecated, Removed, Fixed, Security, and Known limitations.

- Every user-visible, operator-visible, contract, security, migration, compatibility, or release-process change enters `Unreleased` in the same change set.
- Internal refactoring without observable or contractual effect may be omitted.
- On release, move entries from `Unreleased` to `[version] - YYYY-MM-DD`; never rewrite a historical release section except to correct an explicit documentation error.
- Breaking changes begin with `BREAKING:` and link or point to migration guidance.
- Security entries disclose safe impact/remediation information without publishing exploitable secrets or protected findings.

## Release sequence

1. Confirm the included capabilities and unchanged candidate have passed their gates.
2. Select the next version according to this policy.
3. Update `VERSION`, backend and web versions, locks where required, and `CHANGELOG.md` in one release change.
4. Run version consistency, the complete release test matrix, packaging, staging, recovery, and Softwaretest.it reporting.
5. Obtain human release approval.
6. Create the approved `v<version>` tag and public release notes from the changelog.
7. Do not deploy automatically. Production requires its separate approved contract and decision.

## Branch and candidate relationship

Feature, `test`, `staging`, and `main` branches are promotion states, not versions. Tags are labels, not candidate identity. Acceptance remains bound to commit, image digests, manifest, configuration, test definitions, environment, and evidence.
