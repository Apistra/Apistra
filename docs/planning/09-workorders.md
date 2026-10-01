# Workorder Catalogue

Version: 0.6-draft
Status: DRAFT

## Control summary

**Result:** Every planned Apistra workorder has one canonical, AI-executable and objectively verifiable contract file under `docs/workorders/<CAP-ID>/`.
**Change:** Version 0.6 adds an exact status model, separated implementation/evidence/approval states, canonical semantic test IDs, workorder-specific ARCH/SEC applicability, and a validator-enforced dependency graph to the strengthened execution contracts.
**Current position:** 140 workorder contracts exist. All seven CAP-00 workorders are DONE; all business workorders remain DRAFT until their own prerequisite gates and expectation reviews pass.
**Main blocker:** CAP-01 test-definition publication and field-/step-order readback. Its architecture, security, design, path, BDD, fixture-definition, and expectation decisions are approved.
**Next step:** Execute the CAP-01 publication workorder, then mark only an independently executable first CAP-01 implementation workorder READY.

The [canonical workorder index](../workorders/README.md) links every file and its current status.

## Capability directories

- [CAP-00 workorders](../workorders/CAP-00/)
- [CAP-01 workorders](../workorders/CAP-01/)
- [CAP-02 workorders](../workorders/CAP-02/)
- [CAP-03 workorders](../workorders/CAP-03/)
- [CAP-04 workorders](../workorders/CAP-04/)
- [CAP-05 workorders](../workorders/CAP-05/)
- [CAP-06 workorders](../workorders/CAP-06/)
- [CAP-07 workorders](../workorders/CAP-07/)
- [CAP-08 workorders](../workorders/CAP-08/)
- [CAP-09 workorders](../workorders/CAP-09/)
- [CAP-10 workorders](../workorders/CAP-10/)
- [CAP-11 workorders](../workorders/CAP-11/)
- [CAP-12 workorders](../workorders/CAP-12/)
- [CAP-13 workorders](../workorders/CAP-13/)
- [CAP-14 workorders](../workorders/CAP-14/)
- [CAP-15 workorders](../workorders/CAP-15/)
- [CAP-16 workorders](../workorders/CAP-16/)
- [CAP-17 workorders](../workorders/CAP-17/)
- [CAP-18 workorders](../workorders/CAP-18/)

## Common stop conditions

Stop and report when the observed repository contradicts the workorder; a product, architecture, security, design, identity, or ownership decision is missing; scope would expand; an authorised test target or required contract is unavailable; a blocking finding exists; automatic deployment would be introduced; or a business implementation is attempted before CAP-00 and Softwaretest.it readiness pass.

## Readiness rule

A workorder can move from DRAFT/BLOCKED to READY only when its exact paths and current behavior are observed, its generic path placeholder is replaced through reviewed specification revision, prerequisite gates pass, critical expectations are human-confirmed, the independent expectation review is recorded, applicable ADRs/ARCH/SEC rules are approved, its catalogue-listed scenarios and individual manual cases are published and read back from Softwaretest.it, and design references are approved where UI is involved.

Catalogue entries are planning contracts, not permission to implement. Workorder numbers are identifiers rather than execution order; `Required workorders` controls readiness. Each capability owns exactly one test-definition/publication workorder and one final unchanged-candidate staging/human-acceptance workorder.
