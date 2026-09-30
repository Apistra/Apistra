# Softwaretest.it handover contract

This folder is an engineering integration and is deliberately outside the Apistra runtime dependency graph.

The authoritative contracts observed on 2026-09-30 are `https://softwaretest.it/api/v1/openapi.json` (OpenAPI 3.0.3, API version 1.0.0) and `https://softwaretest.it/api/v1/integration-guides/ci.json` (guide version 1.0.0). Authentication uses the `ProjectBearer` bearer scheme. CAP-00 needs `read`, `execution:write`, `testcase:write`, and `ci:write`. The required project token and project identifier must be supplied through protected environment variables and must never enter files or logs.

`preflight.py` verifies both public contracts and, when credentials are present, performs authenticated project, cycle, and CI-report reads. `publisher.py` is safe-by-default: without `--apply` it creates a lossless redacted outbox only. With `--apply`, it creates a CI report, uploads entries, finalises the report, reads the complete report back, compares every submitted field, retrieves all server-side receipts, and writes a redacted atomic evidence file. Every command has a distinct deterministic idempotency key. A reporting retry replays only these HTTP commands; it never reruns tests.

```bash
python engineering/softwaretest/preflight.py --require-reporting
python engineering/softwaretest/publisher.py artifacts/cap00-result-bundle.json --apply --ensure-cycle
```

If a previously rejected command may have been retained by the remote idempotency store after its server-side contract changes, `--command-revision <reasoned-revision>` rotates only the command keys. It does not change or rerun the candidate tests. Arbitrary retry values are prohibited; the revision belongs in the retained receipt.

The default local evidence paths are `artifacts/softwaretest-outbox.json` and `artifacts/softwaretest-roundtrip-receipt.json`. The entire `artifacts/` directory is ignored by Git. A successful receipt contains the selected cycle and started run documents, request hashes, server receipts, receipt readbacks, the report readback, and the comparison result. A failed remote operation retains a machine-readable failure receipt with the stage, error type, redacted detail, request hashes where available, and partial cycle evidence. Receipts never contain the bearer token. `--ensure-cycle` reuses an active or draft cycle named `Apistra CAP-00 Reporting`, or creates it idempotently. Before a draft cycle is started, the publisher requires at least one executable planned run. A `CycleIntent` with status `PLANNED` is not sufficient. If no run exists, the released version configured by `SOFTWARETEST_ANCHOR_VERSION_ID` is added through the cycle-item API, followed by a refreshed revision, a revision-protected cycle start, and a revision-protected run start. Planning dates remain optional.

The publisher follows the guide's read-before-write rule. `REVISION_CONFLICT` causes one bounded refetch, precondition re-evaluation, and a new revision-bound idempotency key. `CYCLE_START_PRECONDITION_FAILED` and `IDEMPOTENCY_CONFLICT` fail closed with the redacted problem code, failed precondition where supplied, and request ID. It never deletes or replaces a cycle in response to a command failure.

Required protected variables:

- `SOFTWARETEST_PROJECT_ID`
- `SOFTWARETEST_TOKEN`

Optional variables:

- `SOFTWARETEST_BASE_URL` (defaults to `https://softwaretest.it`)
- `SOFTWARETEST_CYCLE_ID` (otherwise `--ensure-cycle` resolves the dedicated cycle)
- `SOFTWARETEST_ANCHOR_VERSION_ID` (required only when a draft cycle has no run)

The GitHub job runs automatically on trusted `test`, `staging`, and `main` pushes. Feature branches never receive the protected `softwaretest` environment; their changes must pass through the documented promotion path. Once the workflow is present on the default branch, `workflow_dispatch` offers an explicit opt-in without a new commit.

The 2026-09-30 authenticated preflight proved project, cycle, CI-report-list, definition, and test-case access. The credential UI confirms all four required scopes. A cycle with a directly planned released version was activated successfully; planning dates were incidental. The earlier cycle-start conflict occurred because `CycleIntent=PLANNED` had not produced an executable run, while the API reduced this distinction to generic `409 STATE_CONFLICT`. CI-report creation still returns `404` and automated execution creation returns `409`; this separate automation-resource prerequisite is not described by the public schema. A fresh command revision after the reported server-side fix produced the same `404`, excluding a replayed idempotency failure as the cause. No complete round-trip receipt exists yet, so the CAP-00 gate remains blocked pending controlled lifecycle clarification.
