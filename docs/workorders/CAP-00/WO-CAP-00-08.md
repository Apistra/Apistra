# WO-CAP-00-08 — Publish canonical Steering sources

Version: 0.11-done
Status: DONE
Status reason: GitHub Actions run 37182972206 verified the authenticated import receipts and complete export readback; the product owner reviewed and approved the result on 2026-10-04
Implementation state: COMPLETE
Evidence state: VERIFIED — trusted test run 37182972206 and retained redacted receipt
Approval state: REVIEWED AND HUMAN ACCEPTED — product-owner decision recorded 2026-10-04
Capability: [CAP-00](../../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md)
Assurance: EXTENDED

## Status and traceability

- Requirements: REQ-019, REQ-020
- Process: PRC-07
- Capability contract: ../../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md
- CI test group: TST-WO-CAP-00-08 and CI-TS-19
- Softwaretest.it mapping: PUBLISHED; run 37182972206 imported 160 sources and verified the complete export without drift
- Delivery class: operational-governance
- Owned verification group: TST-WO-CAP-00-08
- Specification revision: 0.11-done

## Risk profile and escalation

EXTENDED applies because this changes `delivery_control` and performs an authenticated external write for every canonical Capability and Workorder. Incorrect status mapping, revision handling, or partial readback could create a misleading project-control view even though it does not change the Apistra product runtime.

Stop if the observed OpenAPI contract changes, the token lacks the confirmed project scope, a source document cannot be mapped without inventing state, an existing external revision conflicts, or full export readback cannot distinguish every submitted source.

## Baselines and contract delta

- Product: ../../planning/01-product-scope.md
- Architecture/patterns: ../../planning/03-architecture.md and ../../planning/11-architecture-decisions-and-patterns.md
- Security: ../../planning/04-security-concept.md
- Delivery and tests: ../../planning/05-delivery-ci-contract.md and ../../testing/test-concept.md
- Delta: add the previously missing, separate Softwaretest.it Steering handover for canonical Capability and Workorder documents; existing test-definition and CI-result publishers remain unchanged.

## Context and current behavior

Runs 37121411402, 37125594799, and 37135598429 successively exposed an undocumented batch limit, an OpenAPI enum collision, and a non-reproducible server receipt hash. The integration was corrected against Guide 1.2.0. Trusted `test` run 37182972206 then accepted 100 plus 60 sources, retained both redacted receipts, and verified every submitted field through the complete export readback.

## Target result

One deterministic manifest represents every canonical `docs/capabilities/CAP-*.md` and `docs/workorders/CAP-*/WO-CAP-*.md` source. CI validates it on every branch. Trusted `test`, `staging`, and `main` runs import it idempotently, retain the server receipt, export the complete Steering state, and fail closed on any missing or changed submitted field.

## Prerequisites

- Dependencies: WO-CAP-00-04, WO-CAP-00-07
- The current Softwaretest.it OpenAPI document confirms Steering import, export, item, list, and overview operations.
- The protected project token has `read` and `steering:write` permission.
- Code conventions and complexity gates CI-TS-17 and CI-TS-18 remain blocking.

## Scope

- Parse stable IDs, source versions, titles, goals, non-goals, risks, explicit states, dependencies, criteria, next steps, source paths, and source observation times from canonical Markdown.
- Reject unknown implementation states, duplicate IDs, invalid versions, empty source classes, unsupported field sizes, or non-reproducible observation timestamps.
- Map source evidence explicitly to the Steering-domain states `MISSING`, `PARTIAL`, `CURRENT`, `FAILED`, `STALE`, and `UNKNOWN`; do not reuse the unrelated file-scan evidence enum currently exposed by the OpenAPI component-name collision.
- Write a lossless local outbox by default and require `--apply` for remote mutation.
- Import deterministic ordered batches of at most 100 items with independent payload-bound idempotency keys, retain every redacted receipt, and compare every submitted item field through one complete export readback.
- Validate Guide 1.2.0 Steering operations, scopes, headers, limits, status domain, failure recovery, and matching OpenAPI list/enum constraints before mutation.
- Reconcile every receipt with `accepted_items + historical_items == submitted items`, validate the remote checksum shape, and retain a rejected remote receipt for diagnosis.
- Add the confirmed operations and scope to public-contract preflight and add a separate protected CI-TS-19 step.
- Document retry, evidence, secret, and runtime-independence boundaries.

## Non-goals and prohibited side effects

- No Apistra product-runtime dependency on Softwaretest.it
- No test-definition, execution, result, deployment, or production behavior change
- No inferred human approval, evidence, transmission, ownership, decision, or completion state
- No destructive remote deletion or archival of missing/renamed sources
- No token, project secret, request authorization header, or unredacted failure payload in artifacts or logs
- No rerun of product tests after a Steering-only transfer failure

## Allowed changes

- `.github/workflows/ci.yml`
- `engineering/softwaretest/`
- `docs/planning/05-delivery-ci-contract.md`
- `docs/planning/00-control-overview.md`
- `docs/planning/09-workorders.md`
- `docs/testing/test-concept.md`
- `docs/capabilities/CAP-00-reproducible-delivery-walking-skeleton.md`
- `docs/capabilities/README.md`
- `docs/workorders/CAP-00/WO-CAP-00-08.md`
- `docs/workorders/README.md`
- `tools/contracts/validate_repository.py`
- `CHANGELOG.md`

An unlisted product, deployment, schema, or dependency change is a stop condition.

## Stop conditions

- The observed OpenAPI contract no longer contains the documented Steering resources, fields, scope, or idempotency behavior.
- A source status, revision, approval, evidence, or transmission state cannot be mapped without inventing information.
- The protected credential is absent, under-scoped, exposed, or resolves to a different project.
- Import acknowledgement or `accepted_items + historical_items` differs, the remote checksum is malformed, or any exported count/submitted readback field differs.
- The change would couple the Apistra runtime to Softwaretest.it, delete remote history, or trigger product deployment or execution.

## Technical guardrails

- The repository Markdown remains authoritative; Softwaretest.it is a verified derived view.
- Source revision is derived only from the explicit semantic document version. A changed document without a version increase must conflict rather than silently replace history.
- `observed_at` is the last Git commit timestamp for the exact source path; authenticated CI checks out full history.
- Missing optional state maps only to the API's explicit unknown/pending values. Unknown mandatory implementation state fails locally.
- One stable source identifier and one payload hash determine idempotency. The same key is reused only for an identical payload.
- Remote receipt/content checksums are validated for shape and retained, while correctness is established by exact field comparison because Guide 1.2.0 does not define the server receipt-checksum preimage.

## ARCH rules and pattern limits

- Rules: ARCH-010, ARCH-012
- Applicability: engineering-adapter isolation, canonical versioned source contracts, deterministic boundary mapping, and protected evidence publication.
- ADRs/patterns: ADR-017 and ADR-019; the adapter remains outside the product runtime and treats the remote system as a derived view.
- A schema-first mapper and explicit status table are required; vendor response models do not enter product-domain code.
- Architecture validation must retain non-empty source discovery plus allowed and failing counterexamples.

## SEC rules and safe test conditions

- Rules: SEC-002, SEC-011, SEC-012, SEC-015
- Applicability: project-scoped bearer authentication, least-privilege Steering writes, redacted evidence, and fail-closed external state verification.
- Feature branches and pull requests perform local validation only; authenticated mutation is restricted to the protected `softwaretest` environment on trusted branches.
- Tests use controlled fake requesters or the authorised project endpoint; no production data, destructive mutation, or token material is permitted.
- Credential absence, insufficient scope, ambiguous response, or unsafe error content blocks the stage.

## Acceptance criteria

1. The local manifest contains every canonical Capability and Workorder exactly once, preserves raw-source and payload hashes, and rejects an empty or duplicate scope.
2. A simulated import proves ordered API-sized payload-bound writes, Steering-domain evidence mapping, current-plus-historical receipt reconciliation for every batch, one full export readback, and failure on a changed field or count.
3. Public preflight verifies Guide 1.2.0 and matching OpenAPI Steering operations, limits, enums, scopes, headers, and recovery rules; CI-TS-19 runs separately from manual-definition publishing and CI-result reporting.
4. A trusted-branch run accounts for every submitted item as accepted or historical, retains a well-formed remote payload checksum, and exports every submitted field without unexplained drift; the redacted receipt is retained.

## Steering criterion evidence

- WO-CAP-00-08-AC-01: status=PASSED; due_now=true; gate=WO-CAP-00-08 completion; reason=Run 37182972206 generated and verified the unique 19-Capability and 141-Workorder manifest with source and content hashes.
- WO-CAP-00-08-AC-02: status=PASSED; due_now=true; gate=WO-CAP-00-08 completion; reason=The hosted adapter suite passed batching, status mapping, receipt reconciliation, export readback, and retained negative cases.
- WO-CAP-00-08-AC-03: status=PASSED; due_now=true; gate=WO-CAP-00-08 completion; reason=The public contract preflight and separate CI-TS-19 step passed in run 37182972206 against Guide 1.2.0.
- WO-CAP-00-08-AC-04: status=PASSED; due_now=true; gate=WO-CAP-00-08 completion; reason=Run 37182972206 accepted 100 plus 60 sources and verified the complete export with no unexplained drift.

## Acceptance examples and test oracles

- **Positive oracle:** the current repository produces 19 Capability and 141 Workorder items with unique IDs; imports are partitioned as 100 plus 60 items and an exact export verifies with no mismatch.
- **Negative oracle:** an unknown document status, duplicate ID, missing source class, changed exported title, invalid checksum, or partial item set fails closed.
- **Idempotency oracle:** replaying the unchanged payload uses the same key and creates no duplicate current item; changed content requires a source revision increase and a new payload-bound key.
- **Security oracle:** no receipt, outbox, error, or log contains the bearer token.

## Expectation sources and independent review

- Sources: the confirmed product-owner request for Steering visibility, the current public Softwaretest.it OpenAPI contract and integration guide observed 2026-10-04, the `$spec-to-workorders` publishing contract, CAP-00, REQ-019/REQ-020, PRC-07, and the linked architecture, security, delivery, and test contracts.
- Positive expectation: one canonical manifest imports all 19 Capabilities and 141 Workorders and exact export readback confirms every submitted field without changing product runtime behavior.
- Counterexample: a successful HTTP response with an unaccounted item, changed source field, malformed remote checksum, invented state, incomplete export, or leaked credential remains a failed result.
- Independent review must compare the implementation, tests, CI boundary, status mappings, and retained evidence with this workorder before DONE; the author may not self-approve unexplained contract drift.

## Required tests

- TST-WO-CAP-00-08-01: complete repository manifest count, unique IDs, and hashes
- TST-WO-CAP-00-08-02: explicit status mapping and unknown-state rejection
- TST-WO-CAP-00-08-03: one idempotent import plus complete export readback
- TST-WO-CAP-00-08-04: count/field/checksum drift and credential absence fail closed
- Existing Ruff, formatting, flake8, complexity, secret-scan, contract, package, and Softwaretest.it preflight gates remain mandatory.

## BDD and manual tests

No new product behavior or operator UI is introduced, so no new BDD or manual process case is allocated. Existing BDD and `MTP-PRC-07` execution evidence remains unchanged. The required observable behavior is owned by TST-WO-CAP-00-08 and CI-TS-19: local manifest validation, authenticated import, receipt verification, complete export readback, and retained redacted evidence.

## Softwaretest.it and CI reporting

CI-TS-19 is a separate Steering stage. Feature branches create and validate only the local manifest. Trusted branches use the protected environment to run preflight, Steering import/readback, manual-definition publishing, and CI-result reporting as separate commands and artifacts. A Steering-only failure retries only the unchanged Steering manifest.

## CI retry and evidence reuse

For an unchanged source manifest, retry only CI-TS-19 with the same payload-bound idempotency key. A changed canonical source, parser, mapping, contract, credential scope, or command revision invalidates the prior Steering evidence and requires local revalidation plus a new trusted-branch roundtrip. Product test and package evidence is reused because this engineering-only transfer cannot change the candidate.

## Deployment and staging evidence

Not applicable to product deployment: this workorder neither builds nor deploys Apistra. Required environment evidence is the trusted branch, protected `softwaretest` environment, source commit, manifest checksum, project identifier, remote receipt, export state checksum, and per-item revision/content checksum. These references must identify one logical transfer attempt.

## Documentation and evidence

- Local outbox: `artifacts/softwaretest-steering-outbox.json`
- Authenticated receipt: `artifacts/softwaretest-steering-receipt.json`
- The receipt records project, source, command revision, complete request-payload checksum, all request-batch checksums and remote receipts, export state checksum, item IDs/revisions/content checksums, and verification result.
- Documentation records the exact API observation date and the distinction between Steering, test definitions, executions, and CI reports.

## Definition of Done

- All four acceptance criteria pass.
- The complete repository and negative fixtures pass locally and in hosted CI.
- CI-TS-19 returns a verified authenticated receipt and complete export readback on the trusted branch.
- An implementation review confirms no invented state, no runtime coupling, and no credential leakage.

## Workorder completion versus capability acceptance

DONE proves only that the canonical planning sources are represented and verified in the external Steering view. It does not alter the already recorded human acceptance of the CAP-00 product candidate, approve a later capability, or grant production approval. The authenticated receipts and complete export comparison are retained from run 37182972206.

## Events, rework, and cost

Record the feature-branch validation, trusted-branch attempt, remote receipt or structured failure, review, rework, and final evidence decision. Unknown duration or cost remains unknown. A transfer-only failure creates no authority to rerun product tests, deploy a candidate, rotate credentials, or modify remote history.

## Dependencies and follow-up

- Upstream capabilities/gates: CAP-00 accepted baseline and protected Softwaretest.it environment
- Required workorders: WO-CAP-00-04, WO-CAP-00-07
- Downstream consumers: every Capability/Workorder readiness view and later Steering status update
- After the authenticated receipt exists, update this workorder's version/status/evidence without rewriting the historical failed or pending state.
