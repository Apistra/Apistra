# CAP-02 — Secrets Endpoints Agents Tools And Limits

Version: 0.2-draft
Status: DRAFT; implementation blocked by prerequisite gates
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can safely configure protected secrets, provider-neutral endpoints, versioned agents, governed tools, and enforceable operating limits.
**Evidence:** Planning contract only; no implementation or acceptance evidence is claimed.
**Main blocker:** Secret encryption and provider-validation details require reviewed decisions.
**Next step:** Complete prerequisite gates and an independent expectation review before implementation READY.

## Goal and value

An Administrator can safely configure protected secrets, provider-neutral endpoints, versioned agents, governed tools, and enforceable operating limits.

## Traceability

- Requirements: REQ-003, REQ-004, REQ-005, REQ-013, REQ-014
- Process: PRC-01
- Product baseline: ../planning/01-product-scope.md
- Architecture and patterns: ../planning/03-architecture.md and ../planning/11-architecture-decisions-and-patterns.md
- Security, delivery, tests, and design: ../planning/04-security-concept.md through ../planning/07-design-contract.md

## Scope

- encrypted secret references
- generative and embedding endpoints
- versioned agents with explicit fallback
- governed tools
- resource and budget limits

## Non-goals

- Work owned by another capability or release
- Automatic deployment or production promotion
- Unreviewed shared-contract, architecture, security, or design changes

## Actors and prerequisites

- Primary actor follows PRC-01.
- Dependencies: CAP-01
- CAP-00 and Softwaretest.it publishing readiness are mandatory before business implementation READY.

## Binding rules

- Secrets are write-only references
- One primary and at most one explicit fallback endpoint per agent
- Dynamic routing is deferred
- Writes require approval unless a narrower policy permits them

## Main flow

1. The authorised actor selects the project and versioned inputs.
2. Apistra validates identity, ownership, policy, schema, limits, and references.
3. The application use case performs the bounded operation through declared ports.
4. State, evidence, diagnostics, and audit data are committed with correlation identifiers.
5. A stable result or safe actionable error is returned.

## Alternative and failure flows

- Invalid, incompatible, unauthorised, or foreign-project input is rejected without data disclosure.
- Retriable failure preserves committed state and cannot duplicate completed effects.
- Policy, limit, approval, and security denials are first-class audited outcomes.

## Data, interfaces, and states

- Mutable administration uses explicit version/conflict handling; published versions are immutable.
- Public contracts are schema-first and versioned; vendor semantics remain in adapters.
- Cross-module access uses public contracts only; secrets remain protected references.
- External effects require idempotency, bounded retry, and stable error translation.

## Architecture, security, and design

- ARCH rules: ARCH-001, ARCH-002, ARCH-003, ARCH-005, ARCH-011, ARCH-012
- SEC rules: SEC-002, SEC-003, SEC-004, SEC-007, SEC-015
- Design references: DSN-005, DSN-006, DSN-019; agent/tool administration references remain pending
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Secret canaries never reappear
2. Endpoint validation is credential-safe
3. Agent versions retain exact references
4. Limit decisions are deterministic and audited

## Test and evidence contract

- Planned automated and manual IDs are defined by the capability test-definition workorder and mapped to process PRC-01.
- Definition, Softwaretest.it publication, fixtures, execution, and reporting are separate evidence states.
- The unchanged candidate runs the complete scope matrix before manual staging acceptance.

## Workorders

- [WO-CAP-02-01](../workorders/CAP-02/WO-CAP-02-01.md)
- [WO-CAP-02-02](../workorders/CAP-02/WO-CAP-02-02.md)
- [WO-CAP-02-03](../workorders/CAP-02/WO-CAP-02-03.md)
- [WO-CAP-02-04](../workorders/CAP-02/WO-CAP-02-04.md)
- [WO-CAP-02-05](../workorders/CAP-02/WO-CAP-02-05.md)
- [WO-CAP-02-06](../workorders/CAP-02/WO-CAP-02-06.md)
- [WO-CAP-02-07](../workorders/CAP-02/WO-CAP-02-07.md)

## Staging and gate

The final workorder deploys the unchanged capability candidate to isolated local staging, executes assigned automated and manual tests, verifies observability and recovery, confirms Softwaretest.it receipts, and requests human acceptance. Workorder DONE, capability acceptance, and production approval remain separate.

## Open decisions

Secret encryption and provider-validation details require reviewed decisions.

No implementing agent may resolve a blocking decision implicitly.

