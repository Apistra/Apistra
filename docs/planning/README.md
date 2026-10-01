# Apistra BuildBySpec Planning Baseline

Version: 0.6-draft
Date: 2026-09-30
Language: English
Assurance profile: EXTENDED
Status: DRAFT

This directory contains the cross-cutting planning baseline for Apistra. Canonical per-item contracts live under `docs/capabilities/` and `docs/workorders/`; the roadmap and catalogue documents here are indexes and gate views.

No document in this baseline is implementation evidence. No capability is implemented, tested, accepted, deployed, or approved merely because it is described here.

## Document map

- 00-control-overview.md — human control view, current status, blockers, and next responsible step
- 01-product-scope.md — product intent, users, scope, non-goals, and product rules
- 02-decision-register.md — confirmed and deferred decisions
- 03-architecture.md — arc42 architecture, binding ARCH rules, and architecture diagrams
- 04-security-concept.md — system-wide security concept and SEC rules
- 05-delivery-ci-contract.md — branch, build, evidence, staging, recovery, and promotion contract
- 06-test-architecture.md — system-centred test model, BPMN process references, and technical evidence paths
- ../testing/test-concept.md — test governance, levels, entry and exit criteria, defect handling, execution, evidence, and acceptance rules
- ../testing/test-id-catalog.md — canonical behavioural scenario IDs, manual package namespaces, and allocation rules
- 07-design-contract.md — brand, interaction, accessibility, and rendered visual design references
- 08-capabilities-and-roadmap.md — gate-based release index; detailed contracts are in `../capabilities/`
- 09-workorders.md — readiness/index view; one execution contract per file is in `../workorders/`
- 10-traceability-and-gates.md — requirement-to-evidence mappings and release gates
- 11-architecture-decisions-and-patterns.md — concrete ADRs, pattern scope, prohibitions, and verification
- 12-repository-path-contract.md — observed repository roots, planned capability package mapping, workorder path boundaries, and unresolved new-root decisions
- ../../VERSIONING.md — product version authority, compatibility meaning, and release procedure
- ../../CHANGELOG.md — curated history of user-visible, contract, security, and operational changes

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
- Test concept: DRAFT
- Versioning and changelog policy: DEFINED; no product release exists
- Design direction: DECIDED, design evidence still PENDING
- Independent expectation review: PENDING
- CAP-00 implementation: ACCEPTED; revision 0.6 hosted evidence, product-owner review, human acceptance, and candidate-bound Softwaretest.it receipts are recorded
- Business implementation: BLOCKED until the separate CAP-01 test-definition publication/read-back gate passes
- Business workorder path contracts: COMPLETE AS PROPOSAL for all 133 workorders; qualified architecture review remains PENDING, with CAP-16 and CAP-17 new-root decisions BLOCKING
