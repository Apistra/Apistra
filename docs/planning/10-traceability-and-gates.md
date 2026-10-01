# Traceability and Gates

Version: 0.5-draft
Status: DRAFT

## 1. Stable requirement catalogue

REQ-001 — Isolated projects within one installation
REQ-002 — Local Administrator authentication and future identity port
REQ-003 — Encrypted project secrets
REQ-004 — Configurable generative and embedding endpoints
REQ-005 — Versioned agents, tools, policies, and limits
REQ-006 — Public connector contract and trusted built-ins
REQ-007 — Full RAG pipeline with provenance and deletion
REQ-008 — Visual and YAML or JSON workflow authoring
REQ-009 — Immutable published workflow versions
REQ-010 — Durable asynchronous execution
REQ-011 — Versioned Process API with idempotency and cancellation
REQ-012 — Human approval for writes by default
REQ-013 — Configurable resource and cost controls
REQ-014 — Restricted runtime network access
REQ-015 — Offline operation
REQ-016 — Local-first observability and audit
REQ-017 — Source-available noncommercial/evaluation and commercial offline licensing
REQ-018 — English documentation and English or German UI
REQ-019 — Controlled branch promotion without automatic deployment
REQ-020 — Softwaretest.it test management and complete result reporting
REQ-021 — Durable advanced control flow
REQ-022 — Scheduled and authenticated event-triggered execution
REQ-023 — Expanded trusted connector catalogue
REQ-024 — Secret-safe import, export, and templates
REQ-025 — Versioned evaluation datasets and provenance
REQ-026 — Calibrated evaluation policies and human review
REQ-027 — Reproducible candidate comparison
REQ-028 — Role-based administration and enterprise identity
REQ-029 — Signed, permission-bounded third-party plugins
REQ-030 — Supported Kubernetes deployment profile
REQ-031 — Commercial operations and optional managed-service boundaries

## 2. Requirement to capability mapping

- REQ-001, REQ-002, REQ-016 → CAP-01
- REQ-003, REQ-004, REQ-005, REQ-013 → CAP-02
- REQ-006, REQ-014 → CAP-03
- REQ-007 → CAP-04
- REQ-008, REQ-009, REQ-018 → CAP-05
- REQ-010, REQ-011, REQ-013, REQ-015, REQ-016 → CAP-06
- REQ-012 → CAP-07
- REQ-017 → CAP-01 and later commercial operations
- REQ-019, REQ-020 → CAP-00 and every capability gate
- REQ-021 → CAP-08
- REQ-022 → CAP-09
- REQ-023 → CAP-10
- REQ-024 → CAP-11
- REQ-025 → CAP-12
- REQ-026 → CAP-13
- REQ-027 → CAP-14
- REQ-028 → CAP-15
- REQ-029 → CAP-16
- REQ-030 → CAP-17
- REQ-017, REQ-031 → CAP-18

## 3. Architecture and security mapping

- Project isolation: ARCH-005; SEC-001; CAP-01
- Secrets: ARCH-003 and ARCH-011; SEC-002; CAP-02
- Provider neutrality: ARCH-003 and ARCH-012; CAP-02 and CAP-03
- Canonical workflow: ARCH-006; CAP-05
- Immutable publication: ARCH-007; SEC-005; CAP-05
- Durable execution: ARCH-008 and ARCH-009; SEC-006; CAP-06
- Human approval: SEC-003 and SEC-015; CAP-07
- Consequential policy decisions: ARCH-015 and ADR-011; CAP-07, CAP-13, CAP-14, and CAP-18
- Egress: ARCH-003; SEC-004 and SEC-016; CAP-02, CAP-03, CAP-06
- Limits: SEC-007; CAP-02 and CAP-06
- Provenance and deletion: SEC-010; CAP-04
- Offline operation: ARCH-010 and ARCH-014; SEC-013; CAP-00 and CAP-06
- Supply chain: SEC-011 and SEC-012; CAP-00
- Licensing: SEC-014; CAP-01 and commercial release

Concrete implementation patterns and their boundaries are defined in `11-architecture-decisions-and-patterns.md`. Each implementation workorder must cite the applicable ADRs rather than treating a pattern as a repository-wide default. The ADR catalogue remains DRAFT globally; the exact CAP-01 slice is approved in `13-cap01-readiness-review.md`.

## 4. Process and test mapping

The stable identifier definitions and intents are governed by the [Canonical Test ID Catalogue](../testing/test-id-catalog.md). A range below is descriptive; each referenced ID remains an individual catalogue entry.

- PRC-01 → CAP-01 → MTP-PRC-01 → BDD-AUTH-001 and BDD-PROJ-001 → MT-PRC-01-001 through MT-PRC-01-006 (`REVIEWED`; not published or executed)
- PRC-02 → CAP-03, CAP-04, and CAP-10 → MTP-PRC-02 → BDD-KNOW-001 and BDD-KNOW-002
- PRC-03 → CAP-05 → MTP-PRC-03 → BDD-WF-001 and BDD-WF-002
- PRC-04 → CAP-06 → MTP-PRC-04 → BDD-RUN-001 through BDD-RUN-003
- PRC-05 → CAP-07 → MTP-PRC-05 → BDD-APPROVAL-001 through BDD-APPROVAL-003
- PRC-06 → CAP-12 through CAP-14 → MTP-PRC-06 → BDD-EVAL-001 through BDD-EVAL-004
- PRC-07 → CAP-00 and operations → MTP-PRC-07 → BDD-OFFLINE-001
- PRC-08 → CAP-08 → MTP-PRC-08 → BDD-FLOW-001 through BDD-FLOW-006
- PRC-09 → CAP-09 → MTP-PRC-09 → BDD-TRIGGER-001 through BDD-TRIGGER-004
- PRC-10 → CAP-11 → MTP-PRC-10 → BDD-PORTABLE-001 through BDD-PORTABLE-004
- PRC-11 → CAP-15 → MTP-PRC-11 → BDD-IAM-001 through BDD-IAM-005
- PRC-12 → CAP-16 → MTP-PRC-12 → BDD-PLUGIN-001 through BDD-PLUGIN-005
- PRC-13 → CAP-17 → MTP-PRC-13 → BDD-K8S-001 through BDD-K8S-003
- PRC-14 → CAP-18 → MTP-PRC-14 → BDD-LIC-001 through BDD-LIC-003 and BDD-MANAGED-001

## 5. Gate sequence

GATE-PLN-01 — Product-owner baseline review

Requires:

- scope and decisions reviewed;
- critical misunderstandings corrected;
- no hidden implementation approval inferred.

GATE-EXP-01 — Independent expectation review

Requires:

- separate derivation from original confirmed decisions;
- comparison and discrepancy resolution;
- human confirmation of critical expectations.

GATE-DES-01 — Design gate

Requires:

- maintainable visual sources;
- rendered references;
- tokens, states, responsive and accessibility contract;
- logo rights and production variants;
- product-owner approval.

GATE-CAP00-READY — Bootstrap workorder readiness

Requires:

- CAP-00 workorders fully expanded;
- permissions and API preflight plan;
- architecture, security, delivery, and test rules approved.

GATE-CAP00-DONE — Delivery foundation

Requires:

- complete bootstrap matrix on exact candidate;
- local staging deployment;
- recovery;
- Softwaretest.it publishing readiness;
- human acceptance.

GATE-WO-READY — Individual business workorder readiness

Requires:

- CAP-00 done;
- exact approved criteria and tests;
- design gate where applicable;
- no blocking decision or finding.

GATE-WO-DONE — Individual workorder completion

Requires:

- implementation and own evidence complete;
- own results reported;
- independent implementation review;
- later capability tests still explicitly assigned.

GATE-CAP-DONE — Capability acceptance

Requires:

- all workorders done;
- complete scope matrix on exact candidate;
- local staging deployment;
- manual tests executed from Softwaretest.it;
- observability and recovery checks;
- human acceptance.

GATE-REL-0X — Release acceptance

Requires:

- all included capabilities accepted;
- cross-capability regression;
- no blocking security or architecture finding;
- legal and public-documentation obligations satisfied;
- human release approval.

GATE-PROD — Production approval

Status: NOT DEFINED

No production release can occur until a production environment contract and explicit human approval exist.

## 6. Evidence identity

Every executed test or gate must bind:

- specification and rule versions;
- repository commit;
- candidate and image digests;
- suite and input fingerprints;
- environment and configuration snapshot;
- relevant identities and policy versions;
- attempt and result;
- Softwaretest.it receipt;
- human approval where required.

## 7. Current gate status

- GATE-PLN-01: PENDING
- GATE-EXP-01: PENDING
- GATE-DES-01: PENDING
- GATE-CAP00-READY: REVIEWED; HUMAN ACCEPTANCE RECORDED
- GATE-CAP00-DONE: VERIFIED; HUMAN ACCEPTANCE RECORDED
- GATE-WO-READY: BLOCKED
- GATE-WO-DONE: BLOCKED
- GATE-CAP-DONE: BLOCKED
- GATE-REL-0X: BLOCKED
- GATE-PROD: NOT DEFINED

## 8. Known evidence gaps

- Detailed Apistra-owned runtime architecture and slice expectations still require qualified review before CAP-06 workorders become READY; ownership is decided by ADR-020
- Authentication is decided by ADR-021; CAP-01 security defaults and tests still require qualified review before affected workorders become READY
- ADR-019 repository layout is approved and implemented; the remaining pattern ADRs still require qualified architecture review
- Softwaretest.it guide 1.1.0 and the authorised CAP-00 project/cycle/report/receipt round-trip are verified by run 36875393087
- Visual reference sources and rendered previews exist, but product-owner approval, logo production assets and rights evidence, accessibility measurement, detailed interaction states, and Softwaretest.it manual UI tests are pending
- Architecture, behavioural, contract, security, supply-chain, packaging, staging, recovery, fixture, and reporting-outbox tooling exists; GitHub Actions run 36618729112 accepted the committed candidate, and product-owner independent review was recorded on 2026-09-30
- GitHub Actions run 36618729112 built the clean committed immutable candidate and passed staging health, controlled failure, and unchanged-image recovery
- Product-owner human bootstrap acceptance was recorded on 2026-09-30; run 36875393087 supplies the final immutable-candidate reporting binding without a material product-behaviour change
- Live branch protection is active for `test`, `staging`, and `main`; mandatory independent approvals remain deferred until a second qualified maintainer is available
- The official AGPLv3 text remains effective for already published revisions; ADR-022 approves the future source-available model, while rights-holder details, transition commit, notices, commercial terms, dependency compatibility, and legal review remain pending before licence-file changes

These are expected planning gaps and must not be represented as failures of implemented software. They remain blockers for their assigned future gates.
