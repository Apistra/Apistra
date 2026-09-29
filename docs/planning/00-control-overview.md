# Human Control Overview

Version: 0.1-draft
Date: 2026-09-29
Scope: Initial Apistra product planning baseline
Profile: EXTENDED

## 1. Intended result

Apistra will be a public, build-in-public platform for designing, testing, publishing, and operating AI-assisted business processes. Published workflow versions expose reliable, versioned APIs and support long-running execution, configurable AI endpoints, knowledge retrieval, tools, and human approvals.

The current deliverable is planning only. It does not include product code, deployment, test execution, Softwaretest.it mutation, or release approval.

## 2. Change from the prior state

The repository currently contains only an initial README, ignore rules, and two logo images. This baseline turns the confirmed discovery decisions into a governed architecture, security model, delivery contract, test architecture, capability roadmap, and executable workorder catalogue.

## 3. Status by control dimension

Implementation:
- No product implementation exists.
- No CI/CD workflow, container image, database schema, or runtime service exists.

Evidence:
- Repository presence and initial assets were inspected.
- No build, test, architecture, security, deployment, recovery, or Softwaretest.it evidence exists yet.
- The public Softwaretest.it OpenAPI endpoint could not be retrieved through the available web reader; API preflight remains a CAP-00 obligation.

Approval:
- Product-owner decisions captured in 02-decision-register.md are DECIDED.
- This planning baseline is DRAFT until reviewed by the product owner.
- Qualified architecture and security review remain PENDING.
- No production approval exists or is requested.

## 4. Blocking obligations

1. The planning package requires human product review.
2. EXTENDED assurance requires an independent expectation review before workorders can become READY.
3. CAP-00 must establish the protected CI path, immutable candidate, local staging deployment, diagnostics, recovery, and evidence reporting.
4. Softwaretest.it OpenAPI, authentication, scopes, resource model, idempotency, and round-trip behaviour must be verified before any write.
5. UI workorders remain blocked until maintainable visual reference sources and rendered views satisfy the design gate.
6. No business workorder may start until CAP-00 and the publishing-readiness gate have passed.

## 5. Next responsible steps

Product owner:
- Review this baseline and either approve it for expectation review or request changes.

Independent reviewer:
- Derive expectations from the confirmed source decisions without using implementation as authority.
- Compare the result with this baseline and record discrepancies.

CAP-00 implementer, only after readiness:
- Implement the minimal walking skeleton and delivery foundation without adding business behaviour.

## 6. Decision required now

No additional product decision is required to draft the baseline. Human approval of the baseline is required before any workorder is promoted from DRAFT or BLOCKED to READY.
