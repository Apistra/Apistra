# Softwaretest.it handover contract

This folder is an engineering integration and is deliberately outside the Apistra runtime dependency graph.

The authoritative contracts observed on 2026-10-01 are `https://softwaretest.it/api/v1/openapi.json` (OpenAPI 3.0.3, API version 1.0.0) and `https://softwaretest.it/api/v1/integration-guides/ci.json` (guide version 1.1.0). Authentication uses the `ProjectBearer` bearer scheme. CI reporting itself requires `read` and `ci:write`; CAP-00 cycle preparation additionally uses `execution:write` and its existing anchor test case uses `testcase:write`. The project token and project identifier must be supplied through protected environment variables and must never enter files or logs.

`preflight.py` verifies both public contracts and, when credentials are present, performs authenticated project, cycle, and CI-report reads. `publisher.py` is safe-by-default: without `--apply` it creates a lossless redacted outbox only. With `--apply`, it creates a CI report, uploads one required-stage result plus every individual test result, finalises the report, reads the complete report back, compares every submitted field, retrieves all server-side receipts, and writes a redacted atomic evidence file. RFC 3339 timestamps are canonicalised to UTC milliseconds before submission so readback remains lossless across the API's documented date-time representation. Every command has a distinct deterministic idempotency key. A reporting retry replays only these HTTP commands; it never reruns tests.

```bash
python engineering/softwaretest/preflight.py --require-reporting
python engineering/softwaretest/publisher.py artifacts/cap00-result-bundle.json --apply --ensure-cycle
```

If a previously rejected command may have been retained by the remote idempotency store after its server-side contract changes, `--command-revision <reasoned-revision>` rotates only the command keys. It does not change or rerun the candidate tests. Arbitrary retry values are prohibited; the revision belongs in the retained receipt.

The default local evidence paths are `artifacts/softwaretest-outbox.json` and `artifacts/softwaretest-roundtrip-receipt.json`. The entire `artifacts/` directory is ignored by Git. A successful receipt contains the selected cycle and started run documents, request hashes, server receipts, receipt readbacks, the report readback, and the comparison result. A failed remote operation retains a machine-readable failure receipt with the stage, error type, redacted detail, request hashes where available, and partial cycle evidence. Receipts never contain the bearer token. `--ensure-cycle` reuses an active or draft cycle named `Apistra CAP-00 Reporting`, or creates it idempotently. Before a draft cycle is started, the publisher requires at least one executable planned run. A `CycleIntent` with status `PLANNED` is not sufficient. If no run exists, the released version configured by `SOFTWARETEST_ANCHOR_VERSION_ID` is added through the cycle-item API, followed by a refreshed revision, a revision-protected cycle start, and a revision-protected run start. Planning dates remain optional.

The publisher follows the guide's read-before-write rule. Cycle commands use `If-Match`; CI-report commands deliberately do not. `REVISION_CONFLICT` causes one bounded refetch, precondition re-evaluation, and a new revision-bound idempotency key. `CYCLE_START_PRECONDITION_FAILED`, `IDEMPOTENCY_CONFLICT`, and `CI_REPORT_CYCLE_NOT_FOUND` fail closed with structured, redacted problem details and the request ID. It never deletes or replaces a cycle in response to a command failure. The latter error's `cycle_id` and `remediation` fields are retained in the failure receipt so that a corrected logical attempt can use an existing project cycle and a new key.

Required protected variables:

- `SOFTWARETEST_PROJECT_ID`
- `SOFTWARETEST_TOKEN`

Optional variables:

- `SOFTWARETEST_BASE_URL` (defaults to `https://softwaretest.it`)
- `SOFTWARETEST_CYCLE_ID` (otherwise `--ensure-cycle` resolves the dedicated cycle)
- `SOFTWARETEST_ANCHOR_VERSION_ID` (required only when a draft cycle has no run)

The GitHub job runs automatically on trusted `test`, `staging`, and `main` pushes. Feature branches never receive the protected `softwaretest` environment; their changes must pass through the documented promotion path. Once the workflow is present on the default branch, `workflow_dispatch` offers an explicit opt-in without a new commit.

Guide 1.1.0 states that `ci_report_create` needs only a bearer credential bound to the URL project and an existing cycle in that project. The cycle build label may differ from `commit_sha`, and no automated definition or pre-provisioned automation resource is required. GitHub Actions run 36875393087 verified this contract against commit `e1619a0d6fe5d5edd7cca1c88a57e5b9845084e6`: one stage and sixteen tests were accepted, the report returned `COMPLETE`/`PASSED`, all submitted fields matched readback, and create, entries, and finalize receipts were `CONFIRMED`. The retained artifact contains no credential material.
