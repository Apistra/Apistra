# CAP-02 — Secrets Endpoints Agents Tools And Limits

Version: 0.7
Status: IN_PROGRESS; WO-CAP-02-06 and WO-CAP-02-01 are DONE, and WO-CAP-02-02 is implemented locally with protected CI and independent review pending
Release: 0.1
Assurance: EXTENDED

## Control summary

**Result:** An Administrator can safely configure protected secrets, provider-neutral endpoints, versioned agents, governed tools, and enforceable operating limits.
**Evidence:** Protected run 37212285531 verified test-definition publication.
PR #31 and protected run 37216514042 verify the reviewed WO-CAP-02-01
implementation, immutable candidate, isolated staging/recovery, Steering,
definition, and receipt round-trips.
WO-CAP-02-02 has local static, architecture, contract, PostgreSQL, backend,
frontend, and coverage evidence on `feature/cap02-endpoint-catalogue`; this is
not protected merge or capability evidence.
**Main blocker:** CAP-02 still requires WO-CAP-02-02 through WO-CAP-02-05 and
the unchanged-candidate acceptance workorder WO-CAP-02-07.
**Next step:** Run protected CI and complete the independent implementation
review for WO-CAP-02-02, then obtain explicit human approval before DONE.

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
- CAP-00 and CAP-01 are accepted. Softwaretest.it Steering and CAP-01
  reporting are operational. Protected run 37212285531 supplied the separate
  CAP-02 publication receipt and exact readback required for implementation.

## Binding rules

- Secrets are write-only references
- One primary and at most one explicit fallback endpoint per agent
- Dynamic routing is deferred
- Writes require approval unless a narrower policy permits them
- Secret envelopes follow ADR-024: AES-256-GCM, versioned key identifiers,
  unique nonces, project-bound authenticated context, and operator-owned keys
  outside the database/repository.
- Endpoint validation follows ADR-025: save is offline; an explicit bounded,
  read-only provider probe validates destination policy before resolving the
  credential and returns only a normalised outcome.
- Tool effects are `READ`, `WRITE`, or `ADMINISTRATIVE`; timeout never grants
  approval.
- Duration, call, token, cost, concurrency, and rate decisions are evaluated
  from one immutable policy version and generate safe attributable audit data.

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

### Secret-key runtime contract

- Persistent secret storage requires `APISTRA_SECRET_KEY_RING_FILE`; the
  protected read-only JSON file contains a `keys` object mapping stable key IDs
  to base64url-encoded 32-byte AES keys. It is never stored in the database,
  repository, image, API, log, or evidence.
- `APISTRA_SECRET_ACTIVE_KEY_ID` identifies the active envelope key without
  containing key material; its default is `local-v1`.
- Rotation adds a new key to the ring and changes the active ID. Previous keys
  remain decrypt-only until a bounded re-encryption step has completed; unknown
  or removed key IDs fail closed.
- `APISTRA_INSTALLATION_ID` participates in authenticated associated data and
  defaults to `local`. Project ID, secret-reference ID, and secret version are
  also bound into the AES-GCM associated data.
- Database-backed startup fails closed when the key file is absent. The
  in-memory local/test adapter may use an ephemeral process key and is not a
  persistent configuration.

## Architecture, security, and design

- ARCH rules: ARCH-001, ARCH-002, ARCH-003, ARCH-005, ARCH-011, ARCH-012
- SEC rules: SEC-002, SEC-003, SEC-004, SEC-007, SEC-015
- Design references: DSN-005, DSN-006, DSN-019, DSN-022, DSN-023; revision
  0.4 was approved by the product owner on 2026-10-04
- Each workorder selects applicable ADRs and pattern boundaries; proposed ADRs are not silently treated as approved.

## Acceptance criteria

1. Secret canaries never reappear
2. Endpoint validation is credential-safe
3. Agent versions retain exact references
4. Limit decisions are deterministic and audited
5. Tool effect classification cannot bypass the active approval policy

## Test and evidence contract

- Planned automated coverage uses `BDD-SECRET-001`, `BDD-ENDPOINT-001`,
  `BDD-AGENT-001`, `BDD-TOOL-001`, and `BDD-LIMIT-001`.
- The CAP-02 extension of `MTP-PRC-01` reserves `MT-PRC-01-007` through
  `MT-PRC-01-014` for secret redaction, cross-project denial, endpoint probing,
  agent-reference immutability, tool approval classification, exact limit
  boundaries, concurrency conflicts, and responsive/accessibility states.
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

The technical readiness decisions, design approval, and human review
independent of the implementing agent are resolved for this draft.

ADR-024, ADR-025, module ownership, and the expanded test scope were confirmed
by the product owner on 2026-10-04. The decisions are recorded in the decision,
architecture, security, design, path, and CAP-02 readiness contracts.

Design revision 0.4 was approved and the independent expectation,
architecture, and security comparison was confirmed complete by the product
owner on 2026-10-04. The eight atomic manual cases and five BDD scenarios were
published and exactly read back in protected run 37212285531. WO-CAP-02-06 is
DONE. WO-CAP-02-01 is also DONE after protected run 37216514042 and explicit
product-owner implementation approval. WO-CAP-02-02 is implemented locally
and awaits protected CI plus independent implementation review. Later
implementation workorders remain DRAFT until their declared predecessor is
complete.

