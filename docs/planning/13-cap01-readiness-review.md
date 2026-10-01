# CAP-01 Readiness Review

Version: 0.2
Date: 2026-10-01
Status: APPROVED; EXTERNAL PUBLISHING GATE CLOSED
Profile: EXTENDED (`authorization`, `tenant_isolation`, `secrets`, `architecture_boundary`)
Scope: CAP-01 planning, architecture, security, design, BDD, manual-test, and fixture-definition readiness

## 1. Control summary

**Result:** CAP-01 has an approved expectation, architecture, security, design,
test-definition, and repository-path baseline. No CAP-01 product implementation,
staging execution, capability acceptance, or production approval is claimed.

**Human decisions:** On 2026-09-30 the product owner accepted the CAP-01
expectation, security, and architecture review; approved design revision 0.3
for DSN-001 through DSN-004; and reviewed the six MT-PRC-01 cases without a
requested correction.

**Evidence state:** Local definitions, BDD scenarios, deterministic fixture
descriptors, tests, and repository contracts are verified. Softwaretest.it
released all six manual definitions and exact field-/ordered-step read-back
matched manifest SHA-256
`b36935d8f0653d95739c259c7a41f3a1c6880ff9d67614111e7e87ce36176e5b`.

**External publishing conclusion:** cycle
`2f5b1800-d187-474f-94ae-5686aefc2d0e` contains released testcase keys
`APISTRA-TC-000002` through `APISTRA-TC-000007`. An immediate unchanged replay
changed zero definitions and created zero execution results. The first
dependency-satisfied implementation workorder may transition to READY after
this workorder is integrated into `test`.

## 2. Independent expectation derivation

Sources:

- REQ-001, REQ-002, REQ-016, and REQ-017 in `10-traceability-and-gates.md`;
- CAP-01 and PRC-01;
- ADR-019 and ADR-021;
- ARCH-001, ARCH-002, ARCH-003, ARCH-004, ARCH-005, ARCH-010 through
  ARCH-012, ARCH-014, and ARCH-015 where assigned by workorder;
- SEC-001, SEC-002, SEC-008, SEC-011, SEC-012, SEC-014, and SEC-015 where
  assigned by workorder;
- design revision 0.3 for DSN-001 through DSN-004.

Derived expectations:

1. A fresh offline installation has no default credential and permits exactly
   one race-safe local Administrator bootstrap.
2. Passwords use Argon2id through an established library. Browser sessions are
   opaque, server-side, rotated where required, revocable, CSRF-protected, and
   transported only through secure HTTP-only same-site cookies.
3. Every project-owned request is authorised against an authenticated project
   context before repository or adapter access. Foreign and unknown projects
   are non-disclosing and indistinguishable to an unauthorised caller.
4. Project commands use explicit version/conflict handling, bounded database
   transactions, typed outcomes, and attributable audit records.
5. Licence status is evaluated offline without exposing signing material and
   without introducing a phone-home dependency.
6. Definition, publication, fixture preparation, execution, reporting, and
   capability acceptance remain separate evidence states.

Comparison found four planning discrepancies, all resolved by this revision:

- canonical module naming is `identity`, replacing the inconsistent
  `identity_admin` label in ADR-001;
- ADR-014 is explicitly assigned to mutable project administration;
- ADR-005 is not applied to CAP-01, and ADR-010 is limited to the
  Softwaretest.it boundary;
- fixture definition is separated from later staging application so test
  preparation does not depend circularly on unimplemented product tables.

No unresolved expectation discrepancy remains inside the CAP-01 planning
scope. A material change to the cited sources invalidates this review.

## 3. Architecture and path decision

CAP-01 uses approved ADR-019 roots and these child boundaries:

- `backend/src/apistra/modules/identity/` for bootstrap, credentials, sessions,
  and the future identity port;
- `backend/src/apistra/modules/projects/` for project ownership and lifecycle;
- `apps/web/src/features/administration/` for DSN-001 through DSN-004;
- the literal contract, test, migration, BDD, fixture, and staging paths listed
  by each CAP-01 workorder.

No additional top-level repository root is authorised. An unlisted path, new
root, private cross-module import, or cross-module table access is a stop
condition.

Pattern applicability is decided as follows:

- WO-CAP-01-01: ADR-001, ADR-002, ADR-003, ADR-004, ADR-013, ADR-017,
  ADR-018, ADR-019, and ADR-021;
- WO-CAP-01-02: ADR-001, ADR-003, ADR-004, ADR-013, ADR-014, ADR-017,
  ADR-018, and ADR-019;
- WO-CAP-01-03: ADR-001, ADR-002, ADR-003, ADR-004, ADR-013, ADR-017,
  ADR-018, ADR-019, and ADR-021;
- WO-CAP-01-04: ADR-002, ADR-010, ADR-013, ADR-017, ADR-018, and ADR-019;
- WO-CAP-01-05: verifies the union of applicable rules and introduces no new
  implementation pattern.

ADR-005 is not applicable: CAP-01 has lifecycle rules but no durable workflow
state machine. Administrator and session persistence use dedicated identity
ports, not a generic repository. Race-safe bootstrap and project commands use
bounded units of work; the Project remains the aggregate root.

## 4. Security review outcome

The approved test boundary requires positive own-project access and negative
anonymous, invalid-credential, revoked-session, foreign-project, direct-route,
and stale-version cases. Tests use only synthetic local/staging data and
protected credential references. Logs, screenshots, fixtures, reports, and
receipts must not contain passwords, session values, signing material, or
foreign-project metadata.

No security exception or residual-risk acceptance is granted. A failure of
identity, project isolation, CSRF/session protection, audit attribution,
secret redaction, or safe fixture targeting blocks the affected workorder.

## 5. Test and fixture readiness

BDD-AUTH-001 and BDD-PROJ-001 are repository definitions under
`tests/bdd/features/cap_01/`. MTP-PRC-01 contains the six reviewed manual
cases. `tools/fixtures/cap_01/` creates deterministic, checksummed synthetic
fixture descriptors without reading credential values or mutating product
state.

Actual application of a descriptor to the unchanged CAP-01 staging candidate,
verification of the resulting identities/data, case execution, and cleanup
remain WO-CAP-01-05 evidence. Local descriptor generation is not presented as
a deployed fixture or passed manual test.

## 6. Gate conclusion

Product, architecture, security, design, path, BDD, manual-definition, local
fixture-definition, and authenticated publication decisions for CAP-01 are
closed. WO-CAP-01-04 is DONE. WO-CAP-01-01 may be moved to READY after this
result is integrated into `test`; later workorders still follow their explicit
dependency chain. No staging execution, behavioral pass, capability
acceptance, or production approval is inferred. A material source change
invalidates the affected receipt and requires explicit change-impact analysis.
