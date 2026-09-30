# CAP-00 test matrix

Status: IMPLEMENTED AND HOSTED VERIFIED; external acceptance pending

- CI-TS-01: repository governance contract plus retained passing and failing fixtures.
- CI-TS-02: Ruff lint/format, TypeScript strict typecheck, and Next.js production build.
- CI-TS-03: AST architecture rules, Import Linter, Dependency Cruiser, cycle checks, and retained forbidden graphs.
- CI-TS-04: Python and TypeScript unit tests with 90% line/function thresholds.
- CI-TS-05: FastAPI health component behavior and safe security headers.
- CI-TS-06: generated API surface against the CAP-00 health contract; Softwaretest.it operation/status contract.
- CI-TS-07: worker heartbeat, idempotent migration, deterministic synthetic fixture setup/reset/cleanup, and concurrent isolation.
- CI-TS-08: BDD-CAP00-001 and BDD-CAP00-002 executed by the candidate staging tool.
- CI-TS-09: secret-pattern scanner with retained detection fixture; non-root/read-only/no-capability container assertions; absent business route.
- CI-TS-10: pip-audit, pnpm audit, digest-pinned bases, locked dependencies, archive checksums, and SPDX SBOM.
- CI-TS-11: the CAP-00 no-schema migration returns the same result repeatedly.
- CI-TS-12: declared CPU, memory, PID, tmpfs, and loopback-port limits. Representative performance thresholds begin with a representative business runtime.
- CI-TS-13: controlled unhealthy worker detection and recovery with unchanged image IDs.
- CI-TS-14: semantic landmarks, label association, dark color scheme, reduced-motion contract, and web unit/build checks. Browser/screen-reader measurement remains assigned to the design gate.
- CI-TS-15: clean-commit image build, local archives, manifest, SBOM, Compose health, marker match, and exact-image verification.
- CI-TS-16: public OpenAPI preflight, all five result statuses, redaction, stable command-specific idempotency, unsupported-status rejection, result bundle, and dry-run outbox. Authenticated write/read verification remains externally blocked.

Stable definitions: `tests/bdd/features/cap00-bootstrap.feature` and `tests/manual/CAP00-MAN-001.md`.

Evidence observed on 2026-09-29: 34 Python tests passed at 96% coverage; two web tests passed at 100% line/function coverage; the web production build, architecture suites, public Softwaretest.it preflight, secret proof fixture, pip-audit, pnpm audit, three image builds, isolated service health, matching web/API markers, absent business route, and recovery to a healthy worker succeeded locally. GitHub Actions run 36618729112 then repeated the five required jobs against committed revision `4f0e67725643afb879baf8033310c4deeff24247` and passed, including candidate packaging, isolated staging, controlled failure, and recovery. Independent review and human bootstrap acceptance were recorded on 2026-09-30. The authenticated Softwaretest.it round-trip, receipt, and exact final-candidate binding remain external gates.
