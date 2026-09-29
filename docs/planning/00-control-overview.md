# Human Control Overview

Version: 0.6-draft
Date: 2026-09-30
Scope: Apistra planning baseline and CAP-00 delivery evidence
Profile: EXTENDED

## 1. Intended result

Apistra is planned as a public build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. The immediate result is a reviewable, traceable product plan with one canonical file per capability and one execution contract per workorder.

## 2. Change from the prior state

Version 0.6 separates workflow status from implementation, evidence, and approval state in all 140 workorders; replaces generated test aliases with one canonical semantic test-ID catalogue; assigns workorder-specific ARCH/SEC applicability; defines ARCH-015 for explicit versioned policy decisions; and makes the repository validator enforce those contracts and the dependency graph.

## 3. Status by control dimension

Implementation:

- CAP-00 health-only web, API, worker, packaging, local-staging, recovery, fixture, and reporting-adapter foundations are implemented.
- CAP-01 through CAP-18 contain planning contracts only; no business capability implementation is claimed.
- No production environment or automatic deployment exists.

Evidence:

- GitHub Actions run 36637376129 passed all five required jobs for commit e57ab19 and the version 0.5 workorder baseline. The version 0.6 correction is locally verified only until it is committed, pushed, and accepted by a new hosted run.
- The expanded repository validator checks exactly CAP-00 through CAP-18, all 140 numbered workorders, exact workflow statuses and separated state fields, canonical test IDs, delivery classes, positive/negative oracles, rule references and applicability, dependency existence and acyclicity, catalogue membership, local links, and forbidden generic boilerplate.
- The public Softwaretest.it OpenAPI preflight and dry-run adapter tests pass; an authenticated project/test-plan round-trip remains unavailable.
- Planning completeness and structural consistency are not human product, architecture, security, design, or capability acceptance.

Approval:

- Confirmed product decisions remain recorded in 02-decision-register.md.
- ADR-019 is approved and implemented; ADR-001 through ADR-018 still require qualified review.
- Design sources exist but the product-owner design gate remains pending.
- No business capability, release, or production approval exists.

## 4. Blocking obligations

1. Configure live branch protection for test, staging, and main.
2. Complete the authorised Softwaretest.it project/test-plan write and field-level read-back.
3. Complete independent expectation and CAP-00 implementation reviews.
4. Record human CAP-00 bootstrap acceptance.
5. Before each business workorder becomes READY, close its named architecture, security, design, test-management, and prerequisite decisions.

## 5. Next responsible steps

Repository administrator:

- Configure branch protection without creating an impossible solo-review policy.

Authorised test-management operator:

- Provide the protected Softwaretest.it project, plan/cycle, and token context for the round-trip.

Independent reviewer and product owner:

- Review CAP-00 evidence and the version 0.6 workorder-contract delta.
- Resolve the remaining architecture/design decisions for the next selected capability.
- Approve no more than one or two independent first workorders as READY.

## 6. Decision required now

No business implementation should begin yet. The next human decision is how branch review will work with the current single repository owner and who performs the independent CAP-00 acceptance review.
