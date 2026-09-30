# MTP-PRC-01 — Administration and Project Lifecycle

Version: 0.1-draft
Status: DRAFT; NOT PUBLISHED; NOT EXECUTED
Process: PRC-01
Capability: [CAP-01](../../../capabilities/CAP-01-installation-and-isolated-project-administration.md)
Owning workorder: [WO-CAP-01-04](../../../workorders/CAP-01/WO-CAP-01-04.md)
Execution owner: [WO-CAP-01-05](../../../workorders/CAP-01/WO-CAP-01-05.md)
Design baseline: [0.3-proposed](../../../planning/07-design-contract.md)

## Package objective

Prove the CAP-01 acceptance boundary through independent, atomic manual cases:
single-use bootstrap, non-disclosing authentication failure, revocable sessions,
isolated project creation with audit, and non-disclosing foreign-project denial.

## Fixture contract

The following fixture identities are specifications, not claims that a generator
already exists:

- `FX-PRC-01-FRESH`: resettable local staging snapshot with no Administrator and
  no project.
- `FX-PRC-01-ADMIN-NO-PROJECT`: completed bootstrap, user `admin.alpha`, no
  authorised project, and protected password parameter
  `STAGING_ADMIN_PASSWORD`.
- `FX-PRC-01-ISOLATION`: completed bootstrap, user `admin.alpha`, authorised
  project `Atlas Research` (`11111111-1111-4111-8111-111111111111`), and an
  existing unauthorised project `Orion Restricted`
  (`22222222-2222-4222-8222-222222222222`). The foreign project is seeded
  directly by the authorised fixture generator; no additional product role or
  user-management UI is implied.

Fixture requirements:

- deterministic reset and verification command;
- idempotent preparation on isolated local staging only;
- no production target and no real personal or customer data;
- protected credential injection without log or screenshot disclosure;
- emitted fixture revision and checksum bound to the execution receipt;
- cleanup by restoring the named snapshot, not by ad hoc destructive UI action.

Fixture implementation state: `NOT AVAILABLE`. Until a reviewed generator and
its verification evidence exist, every case remains blocked for execution.
Fixture-generator delivery and validation belong to WO-CAP-01-04; staging
preparation and case execution belong to WO-CAP-01-05.

## Cases

- [MT-PRC-01-001 — Create the single bootstrap Administrator](MT-PRC-01-001.md)
- [MT-PRC-01-002 — Do not expose a second Administrator bootstrap](MT-PRC-01-002.md)
- [MT-PRC-01-003 — Reject invalid credentials without account disclosure](MT-PRC-01-003.md)
- [MT-PRC-01-004 — Revoke a session and reject its reuse](MT-PRC-01-004.md)
- [MT-PRC-01-005 — Create an isolated project and verify its audit event](MT-PRC-01-005.md)
- [MT-PRC-01-006 — Deny a foreign project without disclosure](MT-PRC-01-006.md)

## Review and publication gates

The package may be published only after all of the following are recorded:

1. product-owner approval or correction of design revision `0.3-proposed`;
2. independent expectation and security review of all six cases;
3. implemented and verified fixtures matching this manifest;
4. open CAP-00 and Softwaretest.it publication gates;
5. schema validation and checksum generation for the unchanged definitions;
6. idempotent Softwaretest.it write and field-/step-order read-back receipts.

Review state: `PENDING`.
Softwaretest.it object IDs: `NOT ASSIGNED`.
Publication receipt: `NOT AVAILABLE`.
