# Human Control Overview

Version: 0.5-draft
Date: 2026-09-29
Scope: Apistra planning baseline and CAP-00 delivery evidence
Profile: EXTENDED

## 1. Intended result

Apistra is planned as a public build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. The immediate result is a reviewable, traceable product plan with one canonical file per capability and one execution contract per workorder.

## 2. Change from the prior state

The previous roadmap and workorder catalogue contained compact summaries. Version 0.5 strengthens all 140 individual workorder contracts with delivery-class-specific results, examples and counterexamples, objective oracles, independent expectation inputs, owned verification groups, explicit dependencies, and evidence invalidation rules. The repository validator now rejects missing contract fields and the former generic boilerplate.

## 3. Status by control dimension

Implementation:

- CAP-00 health-only web, API, worker, packaging, local-staging, recovery, fixture, and reporting-adapter foundations are implemented.
- CAP-01 through CAP-18 contain planning contracts only; no business capability implementation is claimed.
- No production environment or automatic deployment exists.

Evidence:

- Earlier GitHub Actions run 36619441457 passed all five required jobs for commit 15d258a. The later run 36629669025 failed only the Ruff format check; the formatting repair and version 0.5 workorder validation require a new hosted run before they are hosted evidence.
- The expanded repository validator checks exactly CAP-00 through CAP-18, all 140 numbered workorders, required sections, delivery classes, owned test IDs, positive/negative oracles, dependency declarations, catalogue membership, local planning links, and forbidden generic boilerplate.
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

- Review CAP-00 evidence and the version 0.5 workorder-contract delta.
- Resolve the remaining architecture/design decisions for the next selected capability.
- Approve no more than one or two independent first workorders as READY.

## 6. Decision required now

No business implementation should begin yet. The next human decision is how branch review will work with the current single repository owner and who performs the independent CAP-00 acceptance review.
