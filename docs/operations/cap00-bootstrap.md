# CAP-00 bootstrap operations

Status: IMPLEMENTED, human acceptance recorded; awaiting final external reporting evidence and immutable-candidate binding

## Purpose

CAP-00 proves that one committed candidate can be tested, packaged once, deployed manually to isolated local staging, diagnosed, deliberately made unhealthy, and recovered without rebuilding. It contains no business process, identity, connector, model, RAG, or workflow behavior.

## Prerequisites

- Docker Engine with Compose v2
- Python 3.12
- Node.js 24.19.0, Corepack, and pnpm 12.8.1
- uv 0.12.20
- a clean committed checkout

## Local quality gate

Run the same logical stages as GitHub Actions: repository contract fixtures, Ruff checks, Python tests, Import Linter, TypeScript type/architecture/unit tests, production web build, Softwaretest.it adapter tests, secret scan, and dependency audits. `.github/workflows/ci.yml` is the executable command authority.

No stage may pass with an empty test scope. Retained forbidden architecture, repository-contract, and secret fixtures prove that their controls detect violations.

## Build one candidate

From a clean commit:

```text
python tools/release/build_candidate.py
```

The command builds the API, worker, and web images once; saves local OCI-compatible Docker archives; records image IDs and archive SHA-256 values; generates an SPDX 2.3 SBOM; and writes `artifacts/cap00-candidate/candidate-manifest.json` plus its SHA-256 file. Base images, runtime versions, dependencies, and package-manager versions are pinned.

The archive files are the local immutable artefact store for CAP-00. They are intentionally not committed or uploaded by ordinary CI. The compact manifest, checksum, SBOM, result bundle, and reporting outbox are retained by CI for 14 days on a best-effort basis after substantive gates finish.

## Manual isolated staging and recovery

```text
python tools/staging/verify_candidate.py artifacts/cap00-candidate/candidate-manifest.json --run-id local-001
```

Choose a unique run ID. The tool uses loopback-only host ports, a project-specific edge network, an internal bootstrap network, a project-specific volume, read-only non-root containers, dropped capabilities, `no-new-privileges`, and resource limits. It verifies API and web deployment markers, forces the worker into a not-ready state, waits until Docker rejects it as unhealthy, restores the same worker image, verifies all image IDs are unchanged, and removes only the named run resources unless `--keep` was requested.

The Compose file never builds images. No branch or workflow deploys it automatically.

## Evidence and reporting

After the candidate test passes:

```text
python tools/release/create_result_bundle.py artifacts/cap00-candidate/candidate-manifest.json
python engineering/softwaretest/publisher.py artifacts/cap00-result-bundle.json
```

The publisher defaults to a redacted, lossless dry-run outbox. `--apply` is only permitted with protected `SOFTWARETEST_TOKEN` and `SOFTWARETEST_PROJECT_ID` values after repository administration authorises the external write. `SOFTWARETEST_CYCLE_ID` is optional when `--ensure-cycle` is used; a draft cycle without a run additionally requires `SOFTWARETEST_ANCHOR_VERSION_ID`. The adapter validates the published CI guide, follows revision-protected cycle/run commands, and records a redacted field-level receipt. Reporting retries replay only HTTP commands with revision-aware idempotency keys and never rerun tests.

## Final acceptance

Execute [CAP00-MAN-001](../../tests/manual/CAP00-MAN-001.md) independently. CAP-00 closes only after the unchanged committed candidate passes hosted CI, the authenticated Softwaretest.it field-by-field round-trip, branch protection verification, independent implementation review, and an explicit ACCEPTED decision. Production deployment is not defined or authorised.
