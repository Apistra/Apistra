# Apistra BuildBySpec Planning Baseline

Version: 0.1-draft
Date: 2026-09-29
Language: English
Assurance profile: EXTENDED
Status: DRAFT

This directory is the canonical planning baseline for Apistra. It describes the intended product and the gates that must be satisfied before implementation, capability acceptance, or any production release.

No document in this baseline is implementation evidence. No capability is implemented, tested, accepted, deployed, or approved merely because it is described here.

## Document map

- 00-control-overview.md — human control view, current status, blockers, and next responsible step
- 01-product-scope.md — product intent, users, scope, non-goals, and product rules
- 02-decision-register.md — confirmed and deferred decisions
- 03-architecture.md — complete arc42 architecture and binding ARCH rules
- 04-security-concept.md — system-wide security concept and SEC rules
- 05-delivery-ci-contract.md — branch, build, evidence, staging, recovery, and promotion contract
- 06-test-architecture.md — system-centred test model and Softwaretest.it contract
- 07-design-contract.md — brand, interaction, accessibility, and visual design contract
- 08-capabilities-and-roadmap.md — gate-based release slices and capability outcomes
- 09-workorders.md — implementation-ready workorder catalogue and execution order
- 10-traceability-and-gates.md — requirement-to-evidence mappings and release gates

## Governing rules

1. CAP-00 must prove the complete technical delivery path before any business capability implementation begins.
2. Implementation, evidence, and human approval are separate states.
3. Every capability ends with a local staging acceptance workorder on the unchanged candidate.
4. Softwaretest.it is an engineering dependency, not a runtime dependency.
5. Apistra is never deployed automatically. Promotion between test, staging, and main is controlled through pull requests and human gates.
6. All project documentation, source code identifiers, APIs, issues, test definitions, and workorders use English.
7. Product UI is internationalised from the start; English and German are the first locales.

## Current readiness

- Product discovery: COMPLETE
- Critical product decisions: DECIDED
- Architecture baseline: DRAFT
- Security baseline: DRAFT
- Delivery contract: DRAFT
- Test architecture: DRAFT
- Design direction: DECIDED, design evidence still PENDING
- Independent expectation review: PENDING
- CAP-00 implementation: BLOCKED until its workorders pass readiness review
- Business implementation: BLOCKED until CAP-00 and Softwaretest.it publishing readiness pass
