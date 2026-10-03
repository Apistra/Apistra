# Softwaretest.it handover contract

This folder is an engineering integration and is deliberately outside the Apistra runtime dependency graph.

The authoritative contracts observed on 2026-10-03 are `https://softwaretest.it/api/v1/openapi.json` (OpenAPI 3.0.3, API version 1.0.0) and `https://softwaretest.it/api/v1/integration-guides/ci.json` (guide version 1.1.0). Authentication uses the `ProjectBearer` bearer scheme. Steering import requires `read` and `steering:write`; CI reporting requires `read` and `ci:write`; CAP-00 cycle preparation additionally uses `execution:write` and its existing anchor test case uses `testcase:write`. The project token and project identifier must be supplied through protected environment variables and must never enter files or logs.

The 2026-10-03 Steering response exposed an OpenAPI component-name collision: `SteeringItemImportRequest.evidence_status` references the unrelated upload/scan `EvidenceStatusEnum`, while the running Steering serializer accepts `MISSING`, `PARTIAL`, `CURRENT`, `FAILED`, `STALE`, and `UNKNOWN`. The publisher uses the observed Steering-domain values and tests that closed set explicitly. This compatibility note must be removed only after the public schema names and describes a dedicated Steering evidence enum.

`preflight.py` verifies both public contracts and, when credentials are present, performs authenticated project, Steering-export, cycle, and CI-report reads. `steering_publisher.py` parses every canonical Capability and Workorder Markdown source, validates explicit versions/states and complete non-empty scopes, and creates a lossless local manifest by default. With `--apply`, it splits that ordered manifest into imports of at most 100 items, gives every batch its own payload-bound idempotency key, validates every batch receipt, exports the complete project Steering state once, and compares every submitted field. This limit was confirmed by the API's structured validation response on 2026-10-03 but is not yet declared as `maxItems` in the public OpenAPI document. It never creates a test definition, execution, result, deployment, or product-runtime dependency. `definition_publisher.py` independently publishes the six reviewed CAP-01 manual definitions and compares every field and ordered step. `publisher.py` independently publishes CI results, retrieves server receipts, and verifies full report readback. RFC 3339 timestamps are canonicalised to UTC milliseconds before submission so readback remains lossless across the API's documented date-time representation.

```bash
python engineering/softwaretest/preflight.py --require-reporting
python engineering/softwaretest/steering_publisher.py
python engineering/softwaretest/steering_publisher.py --apply
python engineering/softwaretest/definition_publisher.py
python engineering/softwaretest/definition_publisher.py --apply
python engineering/softwaretest/publisher.py artifacts/cap00-result-bundle.json --apply --ensure-cycle
```

If a previously rejected command may have been retained by the remote idempotency store after its server-side contract changes, `--command-revision <reasoned-revision>` rotates only the command keys. It does not change or rerun the candidate tests. Arbitrary retry values are prohibited; the revision belongs in the retained receipt.

The Steering evidence paths are `artifacts/softwaretest-steering-outbox.json` and `artifacts/softwaretest-steering-receipt.json`. The CAP-01 definition paths are `artifacts/softwaretest-cap01-definition-outbox.json` and `artifacts/softwaretest-cap01-definition-receipt.json`; CAP-00 reporting uses `artifacts/softwaretest-outbox.json` and `artifacts/softwaretest-roundtrip-receipt.json`. The entire `artifacts/` directory is ignored by Git. A successful Steering receipt records the complete-manifest checksum, every batch checksum and remote receipt, the complete export state checksum, and every remote item ID, source revision, and content checksum after exact field comparison. The server checksum algorithm is not defined by the public contract, so it is retained but not guessed; correctness is established by each batch's payload-receipt checksum equality and the field-level complete-export comparison. Failed operations retain machine-readable, redacted failure evidence, including already confirmed batches when a later batch fails. Receipts never contain the bearer token.

The publisher follows the guide's read-before-write rule. Cycle commands use `If-Match`; CI-report commands deliberately do not. `REVISION_CONFLICT` causes one bounded refetch, precondition re-evaluation, and a new revision-bound idempotency key. `CYCLE_START_PRECONDITION_FAILED`, `IDEMPOTENCY_CONFLICT`, and `CI_REPORT_CYCLE_NOT_FOUND` fail closed with structured, redacted problem details and the request ID. It never deletes or replaces a cycle in response to a command failure. The latter error's `cycle_id` and `remediation` fields are retained in the failure receipt so that a corrected logical attempt can use an existing project cycle and a new key.

Required protected variables:

- `SOFTWARETEST_PROJECT_ID`
- `SOFTWARETEST_TOKEN`

Optional variables:

- `SOFTWARETEST_BASE_URL` (defaults to `https://softwaretest.it`)
- `SOFTWARETEST_CYCLE_ID` (otherwise `--ensure-cycle` resolves the dedicated cycle)
- `SOFTWARETEST_ANCHOR_VERSION_ID` (required only when a draft cycle has no run)

The GitHub job runs automatically on trusted `test`, `staging`, and `main` pushes. It first imports and verifies the canonical Steering sources, then publishes the CAP-01 definitions, and finally performs the independent CAP-00 result-reporting round-trip. Each handover remains a separate command and receipt. Feature branches never receive the protected `softwaretest` environment; they validate the complete Steering outbox locally and must pass through the documented promotion path. Full Git history is checked out where the manifest is built so each source uses its stable last-change timestamp.

Guide 1.1.0 states that `ci_report_create` needs only a bearer credential bound to the URL project and an existing cycle in that project. The cycle build label may differ from `commit_sha`, and no automated definition or pre-provisioned automation resource is required. GitHub Actions run 36875393087 verified this contract against commit `e1619a0d6fe5d5edd7cca1c88a57e5b9845084e6`: one stage and sixteen tests were accepted, the report returned `COMPLETE`/`PASSED`, all submitted fields matched readback, and create, entries, and finalize receipts were `CONFIRMED`. The retained artifact contains no credential material.
