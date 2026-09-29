# Traceability and Gates

Version: 0.2-draft
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
REQ-017 — AGPL and commercial offline licence
REQ-018 — English documentation and English or German UI
REQ-019 — Controlled branch promotion without automatic deployment
REQ-020 — Softwaretest.it test management and complete result reporting

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

## 3. Architecture and security mapping

- Project isolation: ARCH-005; SEC-001; CAP-01
- Secrets: ARCH-003 and ARCH-011; SEC-002; CAP-02
- Provider neutrality: ARCH-003 and ARCH-012; CAP-02 and CAP-03
- Canonical workflow: ARCH-006; CAP-05
- Immutable publication: ARCH-007; SEC-005; CAP-05
- Durable execution: ARCH-008 and ARCH-009; SEC-006; CAP-06
- Human approval: SEC-003 and SEC-015; CAP-07
- Egress: ARCH-003; SEC-004 and SEC-016; CAP-02, CAP-03, CAP-06
- Limits: SEC-007; CAP-02 and CAP-06
- Provenance and deletion: SEC-010; CAP-04
- Offline operation: ARCH-010 and ARCH-014; SEC-013; CAP-00 and CAP-06
- Supply chain: SEC-011 and SEC-012; CAP-00
- Licensing: SEC-014; CAP-01 and commercial release

Concrete implementation patterns and their boundaries are defined in `11-architecture-decisions-and-patterns.md`. Each implementation workorder must cite the applicable ADRs rather than treating a pattern as a repository-wide default. The ADR catalogue is present but remains DRAFT until qualified architecture review and product-owner acceptance.

## 4. Process and test mapping

- PRC-01 → CAP-01 → MTP-PRC-01 → BDD-AUTH-001 and BDD-PROJ-001
- PRC-02 → CAP-03 and CAP-04 → MTP-PRC-02 → BDD-KNOW-001 and BDD-KNOW-002
- PRC-03 → CAP-05 → MTP-PRC-03 → BDD-WF-001 and BDD-WF-002
- PRC-04 → CAP-06 → MTP-PRC-04 → BDD-RUN-001 through BDD-RUN-003
- PRC-05 → CAP-07 → MTP-PRC-05 → BDD-APPROVAL-001 through BDD-APPROVAL-003
- PRC-06 → CAP-12 through CAP-14 → MTP-PRC-06
- PRC-07 → CAP-00 and operations → MTP-PRC-07 → BDD-OFFLINE-001

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
- GATE-CAP00-READY: BLOCKED
- GATE-CAP00-DONE: BLOCKED
- GATE-WO-READY: BLOCKED
- GATE-WO-DONE: BLOCKED
- GATE-CAP-DONE: BLOCKED
- GATE-REL-0X: BLOCKED
- GATE-PROD: NOT DEFINED

## 8. Known evidence gaps

- No independent expectation review
- No approved ADR for durable execution
- No authentication implementation ADR
- ADR-019 repository layout is approved and implemented; the remaining pattern ADRs still require qualified architecture review
- No verified Softwaretest.it API contract or authorised project
- Visual reference sources and rendered previews exist, but product-owner approval, logo production assets and rights evidence, accessibility measurement, detailed interaction states, and Softwaretest.it manual UI tests are pending
- Architecture test tooling and CI definitions exist; independent implementation review and accepted hosted-run evidence remain pending
- No security control evidence
- No immutable candidate
- No local staging deployment
- No fixture generator
- No automated or manual test execution
- No legal approval of licence texts

These are expected planning gaps and must not be represented as failures of implemented software. They remain blockers for their assigned future gates.
