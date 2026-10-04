# CAP-02 Readiness Review

Version: 0.1
Date: 2026-10-04
Status: IN_REVIEW
Assurance: EXTENDED (`secrets`, `authorization`, `architecture_boundary`)
Baseline commit: `d83810d181374171abc7118b37a5090b6c71bb7f`
Capability revision: CAP-02 0.3-in-review
Workorder revision: 0.7-draft

## Control summary

**Result:** CAP-02 is selected and its product, architecture, security, design,
path, and test-definition delta is now concrete enough for review.

**Implementation:** NOT STARTED. No CAP-02 runtime module, migration, public
contract, web feature, fixture, or behavioural test exists at the baseline.

**Evidence:** The repository observation and planning consistency checks can be
executed locally. Rendered design references are generated but still require
product approval. CAP-02 definitions have not been published to
Softwaretest.it.

**Approval:** The product owner confirmed ADR-024, ADR-025, module ownership,
and the expanded test scope on 2026-10-04. This confirmation is not design
approval, independent expectation review, workorder READY, capability
acceptance, or production approval.

**Next action:** Review the rendered design references and this exact revision.
After approval, complete WO-CAP-02-06 on its own feature branch and retain its
authenticated publication/readback receipt before starting WO-CAP-02-01.

## Baseline and observed delta

At the baseline, the repository contains accepted CAP-00/CAP-01 modules
`identity` and `projects`, CAP-01 administration web code, CAP-01 API contracts,
six CAP-01 manual cases, and one CAP-01 BDD feature. The planned CAP-02 module,
web, migration, focused-test, fixture, and BDD directories do not exist.

The following existing boundaries remain valid:

- modular monolith and `public.py` cross-module rule from ADR-019;
- explicit API/worker composition roots;
- Python and TypeScript style, type, architecture, complexity, security,
  contract, integration, resource, and reporting gates;
- local isolated staging and manual deployment only;
- authenticated Softwaretest.it Steering, definition, and result adapters;
- accepted project isolation and local Administrator identity from CAP-01.

The CAP-02 delta adds no new top-level repository root and no new deployment
product. It introduces three planned backend modules, matching web features,
versioned contracts/migrations, CAP-02 test definitions, and fixture support.

## Confirmed decisions

1. ADR-024 defines authenticated AES-256-GCM secret envelopes, operator-owned
   runtime keys, project/version-bound associated data, write-only values, and
   explicit rotation/rewrap.
2. ADR-025 separates offline endpoint save from an explicit credential-safe,
   provider-specific read-only connection probe with fail-closed egress.
3. `catalog` owns secrets, endpoints, and tools; `agents` owns immutable agent
   versions; `policies` owns approval classifications and limits.
4. The CAP-02 UI comprises DSN-005, DSN-006, DSN-019, DSN-022, and DSN-023.
5. CAP-02 receives five BDD IDs and eight new manual test IDs. Existing CAP-01
   definitions remain historically distinct.

## Architecture and security comparison

The planned module graph is compatible with ADR-019 because all new packages
remain below existing approved roots. Strategy and Anti-Corruption-Layer usage
is justified only for provider variants. The key provider is a security-
relevant port. Agent versions consume exact public references and do not query
private catalogue/policy data. Policy evaluation is deterministic and returns
a versioned decision value; it does not perform an external effect.

The principal risks are secret disclosure, project-reference substitution,
SSRF/rebinding, unsafe provider error propagation, approval bypass, and
resource-limit race conditions. Section 13.1 of the security contract assigns
each risk to a concrete enforcement point and negative control. Any requirement
for a provider SDK in a public/domain signature, a shared database repository,
silent plaintext fallback, implicit generative probe, or private cross-module
import invalidates this review.

An independent reviewer must compare these expectations with the original
product decisions and the final workorder/test contracts. The comparison must
record reviewer, exact revision/checksum, discrepancies, disposition, and any
remaining blocker before a workorder becomes READY.

## Design review package

Design revision 0.4 defines routes, labels, fields, states, responsive rules,
safe errors, accessibility, and exact boundaries for all five pages. The
representative desktop and mobile renderings are maintained from
`docs/visuals/generate_visuals.py`:

- `docs/visuals/design/cap02-administration-desktop.svg` and `.png`
- `docs/visuals/design/cap02-administration-mobile.svg` and `.png`

The references inherit the already selected dark technical direction and
design tokens; no new logo or visual-direction exploration is required. They
remain IN_REVIEW until the product owner explicitly approves or corrects them.

## Test-definition allocation

| Behaviour | Automated BDD | Manual case(s) | Owner |
| --- | --- | --- | --- |
| Secret write-only storage, redaction, foreign/revoked denial | BDD-SECRET-001 | MT-PRC-01-007, MT-PRC-01-008 | WO-CAP-02-01 / final execution WO-CAP-02-07 |
| Offline save and safe endpoint probe | BDD-ENDPOINT-001 | MT-PRC-01-009 | WO-CAP-02-02 / final execution WO-CAP-02-07 |
| Immutable agent references and explicit fallback | BDD-AGENT-001 | MT-PRC-01-010 | WO-CAP-02-03 / final execution WO-CAP-02-07 |
| Tool effect and approval classification | BDD-TOOL-001 | MT-PRC-01-011 | WO-CAP-02-04 / final execution WO-CAP-02-07 |
| Exact limit decision and audit | BDD-LIMIT-001 | MT-PRC-01-012, MT-PRC-01-013 | WO-CAP-02-05 / final execution WO-CAP-02-07 |
| Responsive, keyboard, focus, safe state presentation | not applicable as a separate business E2E | MT-PRC-01-014 | final execution WO-CAP-02-07 |

WO-CAP-02-06 must create complete BDD text and atomic manual definitions,
implement or name the idempotent CAP-02 fixture, generalise the CAP-01-specific
definition publisher without rewriting prior receipts, publish only the CAP-02
set, and verify field/step order through authenticated readback. Publication
does not create an execution result.

## Workorder readiness order

1. **WO-CAP-02-06:** first executable workorder after design and expectation
   approval; owns definitions, fixtures contract, publisher delta, receipt, and
   readback.
2. **WO-CAP-02-01:** secret envelopes/references and DSN-006.
3. **WO-CAP-02-02:** endpoint catalogue/probe and DSN-005.
4. **WO-CAP-02-03:** immutable agent versions/fallback and DSN-022.
5. **WO-CAP-02-04:** tool contracts/effect policy and DSN-023.
6. **WO-CAP-02-05:** limit/policy decisions and DSN-019.
7. **WO-CAP-02-07:** one unchanged-candidate full matrix, local staging,
   recovery, all eight manual cases, reporting, independent implementation
   review, and explicit human capability acceptance.

Numbering is identity, not execution order. Each executable result uses its own
feature branch and pull request into `test`. No branch automatically deploys or
promotes to `staging` or `main`.

## Gate assessment

| Gate | State | Evidence or missing item |
| --- | --- | --- |
| CAP-00/CAP-01 prerequisite | PASS | Accepted baseline on `test` |
| Code quality setup | PASS | Existing formatter, linter, type, complexity, architecture, and negative-fixture gates |
| Product decisions | PASS | 2026-10-04 confirmation; ADR-024 and ADR-025 recorded |
| Repository path mapping | PARTIAL | Product ownership confirmed; independent architecture comparison pending |
| Security definition | PARTIAL | CAP-02 controls defined; qualified comparison pending |
| Design | PENDING | Revision 0.4 and renders require product approval |
| Expectation review | PENDING | Independent derivation/comparison not yet recorded |
| CAP-02 test definitions | PENDING | WO-CAP-02-06 not executed |
| Softwaretest.it CAP-02 publication | PENDING | No CAP-02 receipt/readback exists |
| Product implementation | NOT STARTED | WO-CAP-02-01 through WO-CAP-02-05 remain DRAFT |
| Capability acceptance | NOT DUE | WO-CAP-02-07 remains DRAFT |
| Production approval | NOT GRANTED | Outside this review |

## Readiness decision

CAP-02 planning may proceed through review. No product implementation workorder
is READY at this revision. After explicit design approval and an independent
expectation/architecture/security comparison, WO-CAP-02-06 may be changed to
READY. Behavioural workorders remain blocked until WO-CAP-02-06 is DONE with a
verified Softwaretest.it receipt and readback.
