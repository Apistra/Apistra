# Business Workorder Repository Path Contract

Version: 0.1-proposed
Status: IN_REVIEW
Observation date: 2026-09-30
Observed repository commit: `be7e84d`
Scope: CAP-01 through CAP-18 business workorders
Assurance: EXTENDED (`architecture_boundary`)

## 1. Control summary

**Result:** Every business workorder names existing observed repository paths and
a bounded planned path set instead of delegating path discovery to the
implementing agent.

**Evidence state:** The existing paths were observed in the local WSL checkout
at `/home/jens/projects/apistra`. Planned paths are specifications and are not
implementation evidence.

**Approval state:** IN_REVIEW. ADR-019 already approves the top-level monorepo
roots and module-first structure. The capability-to-package mapping below still
requires the normal expectation and qualified architecture review before an
affected workorder may become READY.

**Main blockers:** `contracts/plugins`, `plugin-sdk/python`, and
`deploy/kubernetes` are new top-level architecture boundaries not covered by
ADR-019. CAP-16 or CAP-17 work that needs them remains BLOCKED until a reviewed
ADR extends ADR-019 or selects an approved existing boundary.

## 2. Observed repository baseline

The following paths existed at the observation commit and are protected by the
current repository architecture checks:

- `apps/web/`
- `apps/web/src/features/`
- `backend/`
- `backend/src/apistra/modules/`
- `backend/src/apistra/modules/projects/`
- `backend/src/apistra/entrypoints/api/composition.py`
- `backend/src/apistra/entrypoints/worker/composition.py`
- `backend/src/apistra/platform/`
- `backend/tests/{architecture,component,contract,integration,unit}/`
- `connector-sdk/python/`
- `contracts/{connectors,events,openapi,workflow}/`
- `deploy/compose/`
- `docs/{capabilities,operations,planning,security,testing,visuals,workorders}/`
- `engineering/softwaretest/`
- `tests/{architecture-fixtures,bdd,manual,security-fixtures}/`
- `tools/{architecture,contracts,fixtures,release,security,staging}/`

Brace notation in this overview is explanatory. Every workorder lists literal
repository paths without brace notation.

Observed paths prove location only. They do not authorise arbitrary changes to
everything below an observed root.

## 3. Planned capability ownership below approved roots

The names below are explicit planned targets. A `PLANNED` label never means the
directory or implementation already exists. Each new backend module must use
the ADR-019 internal structure (`domain`, `application`, `ports`, `adapters`,
and `public.py`) and pass CI-TS-03 before its owning implementation workorder can
be DONE.

- CAP-01: `backend/src/apistra/modules/identity/`, existing
  `backend/src/apistra/modules/projects/`, and
  `apps/web/src/features/administration/`.
- CAP-02: `backend/src/apistra/modules/catalog/`,
  `backend/src/apistra/modules/agents/`,
  `backend/src/apistra/modules/policies/`, and matching web features
  `catalog/`, `agents/`, and `policies/`.
- CAP-03 and CAP-10: `backend/src/apistra/modules/connectors/` and
  `apps/web/src/features/connectors/`; public connector contracts remain under
  `contracts/connectors/` and `connector-sdk/python/`.
- CAP-04: `backend/src/apistra/modules/knowledge/` and
  `apps/web/src/features/knowledge/`.
- CAP-05: `backend/src/apistra/modules/workflows/` and
  `apps/web/src/features/workflows/`.
- CAP-06: `backend/src/apistra/modules/runtime/` and
  `apps/web/src/features/runs/`.
- CAP-07: `backend/src/apistra/modules/human_tasks/`, the public boundaries of
  `runtime/` and `policies/`, and `apps/web/src/features/human-tasks/`.
- CAP-08: the public boundaries of `workflows/`, `runtime/`, and
  `human_tasks/`, plus the `workflows/` and `human-tasks/` web features.
- CAP-09: `backend/src/apistra/modules/triggers/`, the public `runtime/`
  boundary, and `apps/web/src/features/triggers/`.
- CAP-11: `backend/src/apistra/modules/portability/` and
  `apps/web/src/features/portability/`.
- CAP-12 through CAP-14: `backend/src/apistra/modules/evaluations/`, the public
  `policies/` boundary where required, and
  `apps/web/src/features/evaluations/`.
- CAP-15: the `identity/` and `projects/` public boundaries plus
  `apps/web/src/features/identity/` and `apps/web/src/features/settings/`.
- CAP-16: `backend/src/apistra/modules/plugins/` and
  `apps/web/src/features/plugins/`. The proposed `contracts/plugins/` and
  `plugin-sdk/python/` roots remain BLOCKING architecture decisions.
- CAP-17: existing `backend/src/apistra/platform/`, `deploy/compose/`, and
  `docs/operations/`. The proposed `deploy/kubernetes/` root remains a BLOCKING
  architecture decision.
- CAP-18: `backend/src/apistra/modules/licensing/`,
  `apps/web/src/features/licensing/`, existing licensing files at repository
  root, and `docs/operations/`.

## 4. Workorder path-block contract

Every CAP-01 through CAP-18 workorder contains all of the following in
`## Allowed changes`:

1. the observation commit and date;
2. literal `EXISTING` paths confirmed in that checkout;
3. literal `PLANNED` paths authorised only after every READY prerequisite is
   satisfied;
4. a workorder-class boundary explaining which listed paths may change;
5. the rule that an unlisted path, new root, cross-module private import, or
   cross-module table access stops execution and requires reviewed impact.

The path list is an upper bound, not an instruction to touch every path. Scope,
target result, non-goals, ARCH/SEC rules, and tests further narrow it.

Common path rules:

- Product implementation workorders may change only their named module/web
  feature, explicitly named language-neutral contract roots, focused CAP test
  directories, required composition roots, an optional migration directory,
  and directly affected documentation.
- Contract-definition workorders do not authorise product behaviour. They may
  change the named contract/SDK path, contract tests, and directly affected
  documentation.
- Test-definition-and-publication workorders do not authorise product runtime
  changes. They may change local test definitions, fixture definitions, the
  Softwaretest.it engineering adapter, and directly affected documentation.
- Capability-acceptance workorders do not authorise feature implementation.
  They may change staging verification, acceptance definitions/evidence, and
  directly affected documentation; generated evidence remains separate from
  source and is never treated as a pass before execution.
- Design and architecture decisions may change only their named documentation,
  maintainable visual sources, rule implementations/fixtures, and directly
  affected indexes.
- Legal-governance work may change only the named licence/notice/governance
  documents and their directly affected planning indexes.

## 5. Migration and test locations

When a workorder requires persistence, its migrations are planned below
`backend/src/apistra/platform/database/migrations/cap_NN/`. This path is not
permission to introduce a migration unless the workorder's target and
acceptance contract require one.

Focused backend tests are planned below:

- `backend/tests/unit/cap_NN/`
- `backend/tests/component/cap_NN/`
- `backend/tests/contract/cap_NN/`
- `backend/tests/integration/cap_NN/`

BDD definitions are planned below `tests/bdd/features/cap_NN/`. Manual
definitions remain below the process-owned `docs/testing/manual/PRC-NN/` path.
Acceptance evidence is generated below `artifacts/acceptance/CAP-NN/` and must
remain attributable to the exact candidate and environment.

## 6. Review and invalidation

- Path observation must be refreshed if ADR-019, the repository roots, package
  managers, composition roots, or architecture-test configuration changes.
- Adding or moving a top-level root is an `architecture_boundary` change and
  invalidates affected expectation/architecture review.
- Creating a planned module does not by itself approve behavior or satisfy a
  workorder.
- An implementing agent must stop when the observed checkout contradicts a
  listed `EXISTING` path or when the result requires an unlisted path.
- This contract does not change any workorder status, approve any design, open
  a Softwaretest.it gate, or provide implementation evidence.
