# CAP-01 Review, Retest, And Human Acceptance Record

Date: 2026-10-04
Capability: CAP-01 — Installation And Isolated Project Administration
Workorder: WO-CAP-01-05
Decision authority: Product owner
Review result: ACCEPTED
Human acceptance result: ACCEPTED
Production approval: NOT GRANTED

## Accepted scope and candidate

The product owner reviewed the CAP-01 implementation and confirmed that the
manual defect retests were successful. The accepted local-staging execution is
bound to source candidate
`e522266b8d113ddd8e6807669fb3f3abf88e3eae` and run
`cap01-retest-e522266-01`. PR #25 merged the same source tree to protected
`test` as `e348ee5f3b6ef8f11fbcc37e417093540176c66d`.

GitHub Actions run `37192774502` passed contracts/static checks, architecture,
tests, security/supply-chain, candidate packaging, isolated staging/recovery,
and the authenticated Softwaretest.it round-trip for the merged tree.

## Manual execution and defect disposition

Softwaretest.it cycle `420e010d-0e29-4033-b127-ff4ec2400238` contains the six
published CAP-01 manual cases. Five cases have a normal final `PASSED` run:

- APISTRA-TC-000002: `50494c5e-fe95-42e1-afa4-772a003fabdf`
- APISTRA-TC-000003: `26497df3-21b0-44c0-afde-2f58d44664e5`
- APISTRA-TC-000004: `54c296c5-748c-4b0e-ac5e-774941d9c6f7`
- APISTRA-TC-000005 retest: `2fd28de8-7913-4900-9f83-ebaa736303fa`
- APISTRA-TC-000007: `4a0af24a-ecd8-44c2-8fd5-0b3b2842f116`

The initial APISTRA-TC-000005 and APISTRA-TC-000006 runs exposed three defects.
After the fixes were staged, the product owner used Softwaretest.it's direct
defect-retest path and confirmed all retests successful. Authenticated API
read-back then returned:

- APISTRA-D0001 (`111f5e44-fa03-4c48-b3b4-7c509d568630`): `CLOSED`, `FIXED`, revision 5
- APISTRA-D0002 (`f628a867-96fe-47c3-a548-9dfd58bb182b`): `CLOSED`, `FIXED`, revision 5
- APISTRA-D0003 (`91654d64-ce6b-4143-a9c0-313eadef142d`): `CLOSED`, `FIXED`, revision 5

## Accepted Softwaretest.it reporting exception

Softwaretest.it currently has two retest paths with inconsistent status
projection. The direct defect-retest path successfully closed every linked
defect but did not populate the normal RetestDocument list. An unused second
APISTRA-TC-000006 run (`1ce976e7-22f3-458f-b5b0-de310dcf6641`) therefore remains
`NOT_STARTED` with `NOT_RUN` steps.

The product owner explicitly decided on 2026-10-04 that successful direct
retests and the authenticated `CLOSED/FIXED` state of all linked defects are the
authoritative acceptance evidence. The unused repeat-run display is retained as
a known platform reporting exception; it is not relabelled, deleted, or
misrepresented as a passed run.

## Decision and validity

CAP-01 and WO-CAP-01-05 are accepted and DONE for the candidate, local-staging
environment, test definitions, fixture set, and evidence identified above. No
production deployment or production approval is granted.

A material change to CAP-01 behavior, identity/project isolation, session or
CSRF controls, test definitions, fixture semantics, candidate tree, or the
accepted Softwaretest.it exception requires change-impact review and repetition
of the affected gates.
