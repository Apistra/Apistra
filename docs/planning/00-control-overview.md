# Human Control Overview

Version: 0.8
Date: 2026-10-04
Scope: Apistra planning baseline, completed CAP-00 delivery evidence, and CAP-01 acceptance readiness
Profile: EXTENDED

## 1. Intended result

Apistra is planned as a public build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. The immediate result is a reviewable, traceable product plan with one canonical file per capability and one execution contract per workorder.

## 2. Change from the prior state

Version 0.8 closes the separate Softwaretest.it Steering handover from trusted `test` run 37182972206 and the recorded product-owner review. It also reflects completed CAP-01 implementation and definition-publication workorders while preserving the still-open unchanged-candidate fixture and six-case manual acceptance execution. Workflow status remains separate from implementation, evidence, and approval state.

## 3. Status by control dimension

Implementation:

- CAP-00 health-only web, API, worker, packaging, local-staging, recovery, fixture, and reporting-adapter foundations are implemented.
- CAP-01 implementation workorders WO-CAP-01-01 through WO-CAP-01-04 are complete; WO-CAP-01-05 remains the final local-staging and human-acceptance workorder.
- CAP-02 through CAP-18 remain planning contracts only; no implementation is claimed.
- No production environment or automatic deployment exists.

Evidence:

- GitHub Actions run 37182972206 passed all required jobs for commit `0e1079ad80c5ed9cc52c4aebca65631febabb15c`, including contracts/static checks, architecture, tests, security/supply chain, candidate packaging, isolated staging/recovery, and the protected Softwaretest.it round-trip.
- The Steering handover accepted deterministic batches of 100 and 60 sources, retained both receipts, and verified every submitted field through the complete export readback.
- Live branch protection is enabled for `test`, `staging`, and `main`: pull requests, strict required checks, linear history, resolved conversations, administrator enforcement, and force-push/deletion prevention are active. Required approvals and CODEOWNERS reviews are deliberately disabled while the repository has only one maintainer.
- The expanded repository validator checks exactly CAP-00 through CAP-18, all 140 numbered workorders, exact workflow statuses and separated state fields, canonical test IDs, delivery classes, positive/negative oracles, rule references and applicability, dependency existence and acyclicity, catalogue membership, local links, forbidden generic boilerplate, and the existence/safety of every business-workorder `EXISTING` repository path. A retained negative fixture proves that a falsely observed path fails validation.
- Softwaretest.it guide 1.1.0, authenticated preflight, report creation, stage/test import, finalisation, full report readback, and all command-receipt readbacks pass without mismatches.
- Planning completeness and structural consistency are not human product, architecture, security, design, or capability acceptance.

Approval:

- Confirmed product decisions remain recorded in 02-decision-register.md.
- ADR-019 is approved and implemented. ADR-001 through ADR-018 remain proposed globally; the exact CAP-01 pattern slice is approved in 13-cap01-readiness-review.md.
- ADR-020 through ADR-022 are product-owner approved. ADR-022 is implemented by the source-available licence set and the exact boundary recorded in `LICENSE-TRANSITION.md`.
- CAP-00 independent expectation/implementation review and human bootstrap acceptance were recorded on 2026-09-30. WO-CAP-00-08 review and product-owner approval were recorded on 2026-10-04; no production approval is inferred.
- Design revision 0.3 is product-owner approved for DSN-001 through DSN-004; unrelated design references remain in review.
- No business capability, release, or production approval exists.

## 4. Blocking obligations

1. Apply the deterministic CAP-01 fixture to the exact local-staging candidate and retain its secret-free receipt.
2. Execute and record all six published `MT-PRC-01-*` cases in Softwaretest.it without changing the candidate.
3. Review the complete CAP-01 evidence and record explicit human capability acceptance or the exact failing case/step.
4. For later capabilities, close their named architecture, security, design, test-management, and prerequisite decisions; CAP-16 and CAP-17 retain their new-root blockers.

## 5. Next responsible steps

Authorised CAP-01 tester:

- Follow `docs/testing/manual/PRC-01/execution-guide.md`, execute all six published cases on the exact candidate, and retain candidate-, fixture-, step-, screenshot-, and Softwaretest.it execution evidence.

Independent reviewer and product owner:

- Re-review CAP-00 only if change-impact analysis identifies a material change to the accepted behaviour or boundary; CAP-00 and WO-CAP-00-08 are otherwise closed.
- Preserve the approved CAP-01 readiness baseline unless change-impact analysis identifies a material delta.
- Review later capability path mappings when selected; resolve the CAP-16 and CAP-17 new-root blockers before those capabilities become READY.
- Approve no more than one or two independent first workorders as READY.

## 6. Decision required now

No new planning decision is required for CAP-01 manual execution. The product owner must execute or supervise the six published cases and then decide CAP-01 acceptance from the unchanged-candidate evidence. Later capability decisions remain outside this CAP-01 approval. Required PR approvals and CODEOWNERS review must be reconsidered when a second qualified maintainer joins.
