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
- CI-TS-12: deterministic declared CPU, memory, PID, tmpfs, privilege, and loopback-port limits. No latency, throughput, or concurrent-load claim is made without a representative running candidate and controlled environment.
- CI-TS-13: controlled unhealthy worker detection and recovery with unchanged image IDs.
- CI-TS-14: semantic landmarks, label association, dark color scheme, reduced-motion contract, and web unit/build checks. Browser/screen-reader measurement remains assigned to the design gate.
- CI-TS-15: clean-commit image build, local archives, manifest, SBOM, Compose health, marker match, and exact-image verification.
- CI-TS-16: public OpenAPI preflight, all five result statuses, redaction, stable command-specific idempotency, unsupported-status rejection, result bundle, dry-run outbox, and authenticated create/import/finalize/report/receipt round-trip.

Stable definitions: `tests/bdd/features/cap00-bootstrap.feature` and `tests/manual/CAP00-MAN-001.md`.

Evidence observed on 2026-09-29: 34 Python tests passed at 96% coverage; two web tests passed at 100% line/function coverage; the web production build, architecture suites, public Softwaretest.it preflight, secret proof fixture, pip-audit, pnpm audit, three image builds, isolated service health, matching web/API markers, absent business route, and recovery to a healthy worker succeeded locally. GitHub Actions run 36618729112 repeated the five required jobs against committed revision `4f0e67725643afb879baf8033310c4deeff24247`. Independent review and human bootstrap acceptance were recorded on 2026-09-30. On 2026-10-01, run 36875393087 revalidated the complete protected matrix for commit `e1619a0d6fe5d5edd7cca1c88a57e5b9845084e6` and verified the authenticated Softwaretest.it create/import/finalize/report/receipt round-trip with one stage, sixteen tests, no mismatches, and no credential material in the retained receipt.
Run 36877064669 repeated the complete protected matrix for commit `7deb5ed14af0fa00b95d33e4d7174f6554d37356`; its authenticated report was `COMPLETE` and `PASSED` with one required stage, sixteen tests, three confirmed receipts, and no mismatches.
