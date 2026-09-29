# Workorder Catalogue

Version: 0.4-draft
Status: DRAFT

## Control summary

**Result:** Every planned Apistra workorder has one canonical, AI-executable contract file under `docs/workorders/<CAP-ID>/`.
**Change:** This document is now an index and readiness policy; detailed scope and status no longer live in a monolithic duplicate catalogue.
**Current position:** 140 workorder contracts exist. CAP-00 implementation evidence is retained in its files; all business workorders remain DRAFT until prerequisite gates and expectation reviews pass.
**Main blocker:** GATE-CAP00-DONE, authenticated Softwaretest.it publishing readiness, architecture/security/design decisions, and independent expectation review as assigned.
**Next step:** Close CAP-00, select CAP-01, complete its expectation review, then mark only an independently executable first workorder READY.

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

A workorder can move from DRAFT/BLOCKED to READY only when its exact paths and current behavior are observed, prerequisite gates pass, critical expectations are human-confirmed, the independent expectation review is recorded, applicable ADRs/ARCH/SEC rules are approved, test IDs and Softwaretest.it mapping exist, and design references are approved where UI is involved.

Catalogue entries are planning contracts, not permission to implement. The final workorder in every capability owns the unchanged-candidate staging gate and human capability acceptance.
