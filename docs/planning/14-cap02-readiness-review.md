# CAP-02 Readiness Review

Version: 0.8
Date: 2026-10-05
Status: HISTORICAL READINESS SNAPSHOT; see the canonical CAP-02 and Workorder sources for current execution status
Assurance: EXTENDED (`secrets`, `authorization`, `architecture_boundary`)
Baseline commit: `d83810d181374171abc7118b37a5090b6c71bb7f`
Capability revision: CAP-02 0.9
Workorder revision: WO-CAP-02-06 0.9-done; WO-CAP-02-01 0.10-done; WO-CAP-02-02 0.10-done; WO-CAP-02-03 0.11-done; WO-CAP-02-04 0.9-ready

This review records the readiness decision at its stated baseline. Its
implementation/gate rows below are historical, not a live status board. The
current status is maintained in
[CAP-02](../capabilities/CAP-02-secrets-endpoints-agents-tools-and-limits.md)
and the linked canonical Workorders; in particular WO-CAP-02-05 is merged
with protected CI green but still awaits independent implementation review
and explicit human workorder acceptance, while WO-CAP-02-07 remains DRAFT.

## Control summary

**Result:** CAP-02 is selected and its product, architecture, security, design,
path, and test-definition delta is now concrete enough for review.

**Implementation:** WO-CAP-02-01 provides the protected `catalog`
secret-reference slice on `test`; WO-CAP-02-02 adds the endpoint catalogue and
WO-CAP-02-03 adds immutable agent versions with explicit fallback. Tool,
policy, fixture, and acceptance work remains outside those completed results;
WO-CAP-02-04 is now the single READY implementation slice.

**Evidence:** The repository observation and planning consistency checks can be
executed locally. The rendered design references and exact interaction
contract are approved. Protected run 37212285531 published and exactly read
back the CAP-02 definitions.

**Approval:** The product owner confirmed ADR-024, ADR-025, module ownership,
the expanded test scope, and design revision 0.4 on 2026-10-04. A human review
independent of the implementing agent compared the expectation, architecture,
and security contracts for baseline `d83810d181374171abc7118b37a5090b6c71bb7f`;
the product owner reported it complete with no unresolved discrepancy. This is
not capability acceptance, deployment, or production approval.

**Next action:** Implement and review WO-CAP-02-04 on its own feature branch.
Do not begin WO-CAP-02-05 before the governed-tool slice passes protected CI,
independent implementation review, and explicit human approval.

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

Review record: on 2026-10-04, the product owner confirmed completion of a human
review independent of the implementing agent against baseline
`d83810d181374171abc7118b37a5090b6c71bb7f`. The review covered original product
expectations, ADR-024/025, module ownership, security enforcement points,
design revision 0.4, workorder boundaries, and the allocated test scope. No
unresolved discrepancy or blocker was reported. The product owner is the
recorded human confirmer; no personal reviewer identity is invented by this
repository.

## Design review package

Design revision 0.4 defines routes, labels, fields, states, responsive rules,
safe errors, accessibility, and exact boundaries for all five pages. The
representative desktop and mobile renderings are maintained from
`docs/visuals/generate_visuals.py`:

- `docs/visuals/design/cap02-administration-desktop.svg` and `.png`
- `docs/visuals/design/cap02-administration-mobile.svg` and `.png`

The references inherit the already selected dark technical direction and
design tokens; no new logo or visual-direction exploration is required. The
product owner approved them on 2026-10-04. This does not substitute for
responsive/accessibility execution evidence against the eventual candidate.

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
| Repository path mapping | PASS | Product ownership and architecture comparison confirmed on 2026-10-04 |
| Security definition | PASS | CAP-02 controls and qualified comparison confirmed on 2026-10-04 |
| Design | PASS | Revision 0.4 and renders approved on 2026-10-04 |
| Expectation review | PASS | Human comparison independent of the implementing agent confirmed on 2026-10-04 |
| CAP-02 test definitions | PASS | Eight definitions and five BDD scenarios are repository-authoritative |
| Softwaretest.it CAP-02 publication | PASS | Protected run 37212285531; verified manifest `f0166d186cfc12bb8b45c0ade680869d49937f94bd67b3f4fd5837f507f36574` |
| Product implementation | IN PROGRESS | WO-CAP-02-01 DONE from run 37216514042; WO-CAP-02-02 DONE from PR #33, merge `96dfa5e`, and run 37228142970; WO-CAP-02-03 DONE from PR #35, PR #36, merge `86a9211`, and protected run 37267844668; WO-CAP-02-04 READY |
| Capability acceptance | NOT DUE | WO-CAP-02-07 remains DRAFT |
| Production approval | NOT GRANTED | Outside this review |

## Readiness decision

WO-CAP-02-06 and WO-CAP-02-01 through WO-CAP-02-03 are DONE. WO-CAP-02-04 is
the only READY implementation workorder. CAP-02 remains unaccepted, and no release
promotion or production approval is inferred.
