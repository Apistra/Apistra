# Softwaretest.it handover contract

This folder is an engineering integration and is deliberately outside the Apistra runtime dependency graph.

The authoritative contract observed on 2026-09-29 is `https://softwaretest.it/api/v1/openapi.json` (OpenAPI 3.0.3, API version 1.0.0). Authentication uses the `ProjectBearer` bearer scheme. CAP-00 needs `read` and `execution:write`; definition synchronisation additionally needs `testcase:write`. The required project token and project/cycle identifiers must be supplied through protected environment variables and must never enter files or logs.

`preflight.py` verifies the public OpenAPI contract and, when credentials are present, performs an authenticated project read. `publisher.py` is safe-by-default: without `--apply` it creates a lossless redacted outbox only. With `--apply`, it creates a CI report, uploads entries, and finalises the report with a distinct idempotency key for every command. A reporting retry replays only these HTTP commands; it never reruns tests.

Required protected variables:

- `SOFTWARETEST_BASE_URL` (defaults to `https://softwaretest.it`)
- `SOFTWARETEST_PROJECT_ID`
- `SOFTWARETEST_CYCLE_ID`
- `SOFTWARETEST_TOKEN`

The authenticated field-by-field write/read round-trip is intentionally still a CAP-00 gate until authorised credentials exist.
