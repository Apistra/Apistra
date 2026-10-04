# Human Control Overview

Version: 1.1
Date: 2026-10-04
Scope: Apistra planning baseline, accepted CAP-00/CAP-01 evidence, and active CAP-02 delivery
Profile: EXTENDED

## 1. Intended result

Apistra is planned as a public build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. The immediate result is a reviewable, traceable product plan with one canonical file per capability and one execution contract per workorder.

## 2. Change from the prior state

Version 1.1 retains the accepted CAP-01 baseline, closes WO-CAP-02-01 after PR
#31, merge `dfa8319`, protected run 37216514042, and explicit product-owner
implementation approval, and activates WO-CAP-02-02. CAP-02 capability
acceptance is not claimed.

## 3. Status by control dimension

Implementation:

- CAP-00 health-only web, API, worker, packaging, local-staging, recovery, fixture, and reporting-adapter foundations are implemented.
- CAP-01 workorders WO-CAP-01-01 through WO-CAP-01-05 are DONE; CAP-01 is human-accepted for the recorded candidate and local-staging environment.
- CAP-02 is IN PROGRESS at capability revision 0.6. WO-CAP-02-06 and WO-CAP-02-01 are DONE; WO-CAP-02-02 is the only READY implementation workorder. CAP-03 through CAP-18 remain planning contracts only.
- No production environment or automatic deployment exists.

Evidence:

- GitHub Actions run 37182972206 passed all required jobs for commit `0e1079ad80c5ed9cc52c4aebca65631febabb15c`, including contracts/static checks, architecture, tests, security/supply chain, candidate packaging, isolated staging/recovery, and the protected Softwaretest.it round-trip.
- The Steering handover accepted deterministic batches of 100 and 60 sources, retained both receipts, and verified every submitted field through the complete export readback.
- Live branch protection is enabled for `test`, `staging`, and `main`: pull requests, strict required checks, linear history, resolved conversations, administrator enforcement, and force-push/deletion prevention are active. Required approvals and CODEOWNERS reviews are deliberately disabled while the repository has only one maintainer.
- The expanded repository validator checks exactly CAP-00 through CAP-18, all 140 numbered workorders, exact workflow statuses and separated state fields, canonical test IDs, delivery classes, positive/negative oracles, rule references and applicability, dependency existence and acyclicity, catalogue membership, local links, forbidden generic boilerplate, and the existence/safety of every business-workorder `EXISTING` repository path. A retained negative fixture proves that a falsely observed path fails validation.
- Softwaretest.it guide 1.1.0, authenticated preflight, report creation, stage/test import, finalisation, full report readback, and all command-receipt readbacks pass without mismatches.
- Protected run 37192774502 passed the complete CAP-01 merged-tree matrix. Five manual cases have normal passed final runs; the sixth used the direct defect-retest path, after which APISTRA-D0001 through APISTRA-D0003 read back as CLOSED/FIXED at revision 5.
- Protected run 37212285531 published and exactly read back the eight CAP-02 manual definitions and retained the redacted definition/Steering receipts required to start product implementation.
- Protected run 37216514042 passed WO-CAP-02-01 contracts/static analysis, architecture, tests, security/supply-chain, candidate packaging, isolated staging/recovery, Steering, CAP-01/CAP-02 definition, and receipt-readback gates for merge `dfa8319`.
- Planning completeness and structural consistency are not human product, architecture, security, design, or capability acceptance.

Approval:

- Confirmed product decisions remain recorded in 02-decision-register.md.
- ADR-019 is approved and implemented. ADR-001 through ADR-018 remain proposed globally; the exact CAP-01 pattern slice is approved in 13-cap01-readiness-review.md.
- ADR-020 through ADR-022 are product-owner approved. ADR-022 is implemented by the source-available licence set and the exact boundary recorded in `LICENSE-TRANSITION.md`.
- CAP-00 independent expectation/implementation review and human bootstrap acceptance were recorded on 2026-09-30. WO-CAP-00-08 review and product-owner approval were recorded on 2026-10-04; no production approval is inferred.
- Design revision 0.3 is product-owner approved for DSN-001 through DSN-004. CAP-02 revision 0.4 is product-owner approved; unrelated design references remain in review.
- CAP-01 human acceptance is recorded. No release promotion or production approval exists.

## 4. Blocking obligations

1. For CAP-02, implement and review WO-CAP-02-02 before activating WO-CAP-02-03; retain WO-CAP-02-07 as the unchanged-candidate manual acceptance owner.
2. Keep the CAP-01 direct-retest reporting exception visible until Softwaretest.it reconciles its two retest status paths; it does not reopen the accepted product behavior while all linked defects remain CLOSED/FIXED.
3. CAP-16 and CAP-17 retain their new-root blockers.

## 5. Next responsible steps

Independent reviewer and product owner:

- Re-review CAP-00 only if change-impact analysis identifies a material change to the accepted behaviour or boundary; CAP-00 and WO-CAP-00-08 are otherwise closed.
- Preserve the approved CAP-01 readiness baseline unless change-impact analysis identifies a material delta.
- Use `docs/testing/manual/PRC-01/acceptance-record.md` as the human decision and exception record for CAP-01.
- Preserve the approved WO-CAP-02-01 result unless change-impact analysis identifies a material delta; retain WO-CAP-02-07 as the owner of manual execution and capability acceptance.
- Review later capability path mappings when selected; resolve the CAP-16 and CAP-17 new-root blockers before those capabilities become READY.
- Approve no more than one or two independent first workorders as READY.

## 6. Decision required now

No new product decision is required before WO-CAP-02-02 execution. Its
implementation must still receive an independent review after protected CI.
The completed WO-CAP-02-01 approval does not approve capability acceptance,
release promotion, or production. Required PR approvals and CODEOWNERS review
must be reconsidered when a second qualified maintainer joins.
