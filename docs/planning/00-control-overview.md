# Human Control Overview

Version: 0.6-draft
Date: 2026-09-30
Scope: Apistra planning baseline and CAP-00 delivery evidence
Profile: EXTENDED

## 1. Intended result

Apistra is planned as a public build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. The immediate result is a reviewable, traceable product plan with one canonical file per capability and one execution contract per workorder.

## 2. Change from the prior state

Version 0.7 preserves the version 0.6 execution contract across all 141 workorders and adds a separate, fail-closed Softwaretest.it Steering handover for the 19 canonical capabilities and 141 canonical workorders. Workflow status remains separate from implementation, evidence, and approval state; test IDs remain canonical and semantic; workorder-specific ARCH/SEC applicability and the dependency graph remain validator-enforced. The 133 business workorders continue to contain literal observed and planned repository path boundaries derived from ADR-019 and the observed `be7e84d` checkout instead of a shared placeholder.

## 3. Status by control dimension

Implementation:

- CAP-00 health-only web, API, worker, packaging, local-staging, recovery, fixture, and reporting-adapter foundations are implemented.
- CAP-01 through CAP-18 contain planning contracts only; no business capability implementation is claimed.
- No production environment or automatic deployment exists.

Evidence:

- GitHub Actions run 36875393087 passed all required jobs for commit `e1619a0d6fe5d5edd7cca1c88a57e5b9845084e6`, including contracts/static checks, architecture, tests, security/supply chain, candidate packaging, isolated staging/recovery, and the protected Softwaretest.it round-trip.
- Live branch protection is enabled for `test`, `staging`, and `main`: pull requests, strict required checks, linear history, resolved conversations, administrator enforcement, and force-push/deletion prevention are active. Required approvals and CODEOWNERS reviews are deliberately disabled while the repository has only one maintainer.
- The expanded repository validator checks exactly CAP-00 through CAP-18, all 140 numbered workorders, exact workflow statuses and separated state fields, canonical test IDs, delivery classes, positive/negative oracles, rule references and applicability, dependency existence and acyclicity, catalogue membership, local links, forbidden generic boilerplate, and the existence/safety of every business-workorder `EXISTING` repository path. A retained negative fixture proves that a falsely observed path fails validation.
- Softwaretest.it guide 1.1.0, authenticated preflight, report creation, stage/test import, finalisation, full report readback, and all command-receipt readbacks pass without mismatches.
- Planning completeness and structural consistency are not human product, architecture, security, design, or capability acceptance.

Approval:

- Confirmed product decisions remain recorded in 02-decision-register.md.
- ADR-019 is approved and implemented. ADR-001 through ADR-018 remain proposed globally; the exact CAP-01 pattern slice is approved in 13-cap01-readiness-review.md.
- ADR-020 through ADR-022 are product-owner approved. ADR-022 is implemented by the source-available licence set and the exact boundary recorded in `LICENSE-TRANSITION.md`.
- CAP-00 independent expectation/implementation review and human bootstrap acceptance were recorded on 2026-09-30; no production approval is inferred.
- Design revision 0.3 is product-owner approved for DSN-001 through DSN-004; unrelated design references remain in review.
- No business capability, release, or production approval exists.

## 4. Blocking obligations

1. Publish and read back the separate CAP-01 BDD/manual test-definition package through the now-verified Softwaretest.it integration.
2. Move only the independently executable first CAP-01 workorder to READY after that publication receipt is reviewed.
3. For later capabilities, close their named architecture, security, design, test-management, and prerequisite decisions.
4. The CAP-01 capability-to-package mapping is approved. CAP-02 through CAP-18 remain in review; CAP-16 and CAP-17 retain their new-root blockers.

## 5. Next responsible steps

Authorised test-management operator:

- Publish the reviewed CAP-01 definitions and retain field-/step-order readback evidence.

Independent reviewer and product owner:

- Re-review CAP-00 only if change-impact analysis identifies a material change to the accepted behaviour or boundary.
- Preserve the approved CAP-01 readiness baseline unless change-impact analysis identifies a material delta.
- Review later capability path mappings when selected; resolve the CAP-16 and CAP-17 new-root blockers before those capabilities become READY.
- Approve no more than one or two independent first workorders as READY.

## 6. Decision required now

CAP-00 is accepted, but no CAP-01 product implementation should begin until the separate CAP-01 definition-publication receipt closes its remaining readiness gap. CAP-01 planning, security, architecture, path, design, BDD, manual-case, and fixture-definition decisions are recorded. Later capability decisions remain outside this CAP-01 approval. Required PR approvals and CODEOWNERS review must be reconsidered when a second qualified maintainer joins.
