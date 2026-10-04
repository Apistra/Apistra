# Softwaretest.it handover contract

This folder is an engineering integration and is deliberately outside the Apistra runtime dependency graph.

The authoritative contracts observed on 2026-10-04 are `https://softwaretest.it/api/v1/openapi.json` (OpenAPI 3.0.3, API version 1.0.0) and `https://softwaretest.it/api/v1/integration-guides/ci.json` (guide version 1.2.0). Authentication uses the `ProjectBearer` bearer scheme. Steering import requires `steering:write`; Steering readback requires `read`; CI reporting requires `read` and `ci:write`; CAP-00 cycle preparation additionally uses `execution:write` and its existing anchor test case uses `testcase:write`. The project token and project identifier must be supplied through protected environment variables and must never enter files or logs.

Guide 1.2.0 and the OpenAPI now agree on the dedicated `SteeringEvidenceStatusEnum`, deterministic batches of one to 100 items, maximum criteria/decision counts, stable source identities, monotonic revisions, independent batch idempotency, and complete export readback. The public guide does not define how the server canonicalises validated data for its receipt `payload_sha256`; the publisher therefore validates and retains that server attestation without guessing its preimage. Request idempotency remains bound to Apistra's independently calculated request-payload hash, while semantic correctness is established by exact complete-export field comparison.

`preflight.py` verifies both public contracts and, when credentials are present, performs authenticated project, Steering-export, cycle, and CI-report reads. `steering_publisher.py` parses every canonical Capability and Workorder Markdown source, validates explicit versions/states and complete non-empty scopes, and creates a lossless local manifest by default. Source status is interpreted by its leading state token, so explanatory text such as `DRAFT; implementation blocked by prerequisite gates` remains planned work rather than an active blocker. Approval is scoped to the imported item: an explicit completed workorder review remains approved even when a later capability or production gate remains open, while explicit `NOT APPROVED`, `NOT YET APPROVED`, and `NOT ACCEPTED` states remain open. Acceptance criteria remain `UNKNOWN` and `due_now=false` because the current Markdown contract contains neither criterion-level results nor criterion-level due gates; item implementation or aggregate evidence must never be promoted into invented criterion evidence. The source revision combines the document version with an explicit projection revision, allowing corrected mapping semantics to advance monotonically without rewriting all canonical documents. With `--apply`, the publisher splits that ordered manifest into imports of at most 100 items, gives every batch its own payload-bound idempotency key, validates every batch receipt, accepts current plus historical counts only when their sum equals the submitted batch, exports the complete project Steering state once, and compares every submitted field. It never creates a test definition, execution, result, deployment, or product-runtime dependency. `definition_publisher.py` independently publishes the six reviewed CAP-01 manual definitions and compares every field and ordered step. `publisher.py` independently publishes CI results, retrieves server receipts, and verifies full report readback. RFC 3339 timestamps are canonicalised to UTC milliseconds before submission so readback remains lossless across the API's documented date-time representation.

```bash
python engineering/softwaretest/preflight.py --require-reporting
python engineering/softwaretest/steering_publisher.py
python engineering/softwaretest/steering_publisher.py --apply
python engineering/softwaretest/definition_publisher.py
python engineering/softwaretest/definition_publisher.py --apply
python engineering/softwaretest/publisher.py artifacts/cap00-result-bundle.json --apply --ensure-cycle
```

If a previously rejected command may have been retained by the remote idempotency store after its server-side contract changes, `--command-revision <reasoned-revision>` rotates only the command keys. It does not change or rerun the candidate tests. Arbitrary retry values are prohibited; the revision belongs in the retained receipt.

The Steering evidence paths are `artifacts/softwaretest-steering-outbox.json` and `artifacts/softwaretest-steering-receipt.json`. The CAP-01 definition paths are `artifacts/softwaretest-cap01-definition-outbox.json` and `artifacts/softwaretest-cap01-definition-receipt.json`; CAP-00 reporting uses `artifacts/softwaretest-outbox.json` and `artifacts/softwaretest-roundtrip-receipt.json`. The entire `artifacts/` directory is ignored by Git. A successful Steering receipt records the complete-manifest checksum, every request-payload checksum and remote receipt, the complete export state checksum, and every remote item ID, source revision, and content checksum after exact field comparison. The server checksum algorithm is not defined by the public contract, so its well-formed SHA-256 attestation is retained but its preimage is not guessed; correctness is established by receipt count reconciliation and the field-level complete-export comparison. Failed operations retain machine-readable, redacted failure evidence, including the rejected remote receipt and already confirmed batches. Receipts never contain the bearer token.

The publisher follows the guide's read-before-write rule. Cycle commands use `If-Match`; CI-report commands deliberately do not. `REVISION_CONFLICT` causes one bounded refetch, precondition re-evaluation, and a new revision-bound idempotency key. `CYCLE_START_PRECONDITION_FAILED`, `IDEMPOTENCY_CONFLICT`, and `CI_REPORT_CYCLE_NOT_FOUND` fail closed with structured, redacted problem details and the request ID. It never deletes or replaces a cycle in response to a command failure. The latter error's `cycle_id` and `remediation` fields are retained in the failure receipt so that a corrected logical attempt can use an existing project cycle and a new key.

Required protected variables:

- `SOFTWARETEST_PROJECT_ID`
- `SOFTWARETEST_TOKEN`

Optional variables:

- `SOFTWARETEST_BASE_URL` (defaults to `https://softwaretest.it`)
- `SOFTWARETEST_CYCLE_ID` (otherwise `--ensure-cycle` resolves the dedicated cycle)
- `SOFTWARETEST_ANCHOR_VERSION_ID` (required only when a draft cycle has no run)

The GitHub job runs automatically on trusted `test`, `staging`, and `main` pushes. It first imports and verifies the canonical Steering sources, then publishes the CAP-01 definitions, and finally performs the independent CAP-00 result-reporting round-trip. Each handover remains a separate command and receipt. Feature branches never receive the protected `softwaretest` environment; they validate the complete Steering outbox locally and must pass through the documented promotion path. Full Git history is checked out where the manifest is built so each source uses its stable last-change timestamp.

Guide 1.2.0 retains the verified CI-reporting contract from 1.1.0: `ci_report_create` needs only a bearer credential bound to the URL project and an existing cycle in that project. The cycle build label may differ from `commit_sha`, and no automated definition or pre-provisioned automation resource is required. GitHub Actions run 36875393087 verified this contract against commit `e1619a0d6fe5d5edd7cca1c88a57e5b9845084e6`: one stage and sixteen tests were accepted, the report returned `COMPLETE`/`PASSED`, all submitted fields matched readback, and create, entries, and finalize receipts were `CONFIRMED`. The retained artifact contains no credential material.
