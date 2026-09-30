# Human Control Overview

Version: 0.6-draft
Date: 2026-09-30
Scope: Apistra planning baseline and CAP-00 delivery evidence
Profile: EXTENDED

## 1. Intended result

Apistra is planned as a public build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. The immediate result is a reviewable, traceable product plan with one canonical file per capability and one execution contract per workorder.

## 2. Change from the prior state

Version 0.6 separates workflow status from implementation, evidence, and approval state in all 140 workorders; replaces generated test aliases with one canonical semantic test-ID catalogue; assigns workorder-specific ARCH/SEC applicability; defines ARCH-015 for explicit versioned policy decisions; and makes the repository validator enforce those contracts and the dependency graph. The 133 business workorders now also contain literal observed and planned repository path boundaries derived from ADR-019 and the observed `be7e84d` checkout instead of a shared placeholder.

## 3. Status by control dimension

Implementation:

- CAP-00 health-only web, API, worker, packaging, local-staging, recovery, fixture, and reporting-adapter foundations are implemented.
- CAP-01 through CAP-18 contain planning contracts only; no business capability implementation is claimed.
- No production environment or automatic deployment exists.

Evidence:

- GitHub Actions run 36637376129 passed all five required jobs for commit e57ab19 and the version 0.5 workorder baseline. Version 0.6 run 36645427566 passed four jobs but exposed Ruff B023 closure binding errors in the repository validator; the repair requires a new hosted run.
- Live branch protection is enabled for `test`, `staging`, and `main`: pull requests, strict required checks, linear history, resolved conversations, administrator enforcement, and force-push/deletion prevention are active. Required approvals and CODEOWNERS reviews are deliberately disabled while the repository has only one maintainer.
- The expanded repository validator checks exactly CAP-00 through CAP-18, all 140 numbered workorders, exact workflow statuses and separated state fields, canonical test IDs, delivery classes, positive/negative oracles, rule references and applicability, dependency existence and acyclicity, catalogue membership, local links, forbidden generic boilerplate, and the existence/safety of every business-workorder `EXISTING` repository path. A retained negative fixture proves that a falsely observed path fails validation.
- The public Softwaretest.it OpenAPI preflight and dry-run adapter tests pass; an authenticated project/test-plan round-trip remains unavailable.
- Planning completeness and structural consistency are not human product, architecture, security, design, or capability acceptance.

Approval:

- Confirmed product decisions remain recorded in 02-decision-register.md.
- ADR-019 is approved and implemented; ADR-001 through ADR-018 still require qualified review.
- ADR-020 through ADR-022 are product-owner approved. ADR-022 is implemented by the source-available licence set and the exact boundary recorded in `LICENSE-TRANSITION.md`.
- CAP-00 independent expectation/implementation review and human bootstrap acceptance were recorded on 2026-09-30; no production approval is inferred.
- Design sources exist but the product-owner design gate remains pending.
- No business capability, release, or production approval exists.

## 4. Blocking obligations

1. Complete the authorised Softwaretest.it project/test-plan write and field-level read-back.
2. Bind the Softwaretest.it receipt, complete required matrix, staging environment, and recorded human decision to the same immutable final candidate.
3. Before each business workorder becomes READY, close its named architecture, security, design, test-management, and prerequisite decisions.
4. Review the proposed capability-to-package mapping in `12-repository-path-contract.md`; CAP-16 additionally needs a decision for plugin contract/SDK roots, and CAP-17 needs a decision for the Kubernetes deployment root.

## 5. Next responsible steps

Authorised test-management operator:

- Provide the protected Softwaretest.it project, plan/cycle, and token context for the round-trip.

Independent reviewer and product owner:

- Re-review CAP-00 only if change-impact analysis identifies a material change to the accepted behaviour or boundary.
- Complete the detailed architecture/security expectation review for the next selected capability.
- Review and accept or correct the proposed business repository path contract; resolve the CAP-16 and CAP-17 new-root blockers before those capabilities become READY.
- Approve no more than one or two independent first workorders as READY.

## 6. Decision required now

No business implementation should begin until GATE-CAP00-DONE and publishing readiness close. The CAP-00 review and human acceptance decisions are recorded. The next external step is the provider fix and authenticated receipt; the next internal decisions concern detailed CAP-01 security defaults and the CAP-06 runtime slices. Required PR approvals and CODEOWNERS review must be reconsidered when a second qualified maintainer joins.
