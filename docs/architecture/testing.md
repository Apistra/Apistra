# Architecture test system

Status: IMPLEMENTED FOUNDATION

The architecture suite turns the approved repository and dependency decisions into executable checks. It is deliberately limited to structure and dependency direction; it does not prove business behaviour, runtime recovery, deployment, security compliance, or release readiness.

## Enforced rules

- `ARCH-001`: Python domain code cannot import framework, ORM, provider, vector-store, or durable-engine dependencies.
- `ARCH-002`: application code cannot depend on adapters or entrypoints.
- `ARCH-003`: ports remain inward-facing and provider-neutral.
- `ARCH-010`: the Softwaretest.it adapter remains outside the runtime dependency graph.
- `ARCH-011`: concrete adapters are assembled only in explicit API or worker composition roots.
- `ARCH-012`: TypeScript entrypoints and features consume public feature contracts rather than another feature's internals.
- `ARCH-013`: Python and TypeScript dependency graphs are acyclic.
- `ARCH-MODULE-PUBLIC`: backend modules may cross a module boundary only through `modules.<name>.public`.
- `ARCH-SCOPE`: an empty source scope fails instead of reporting a false success.

Python uses Import Linter for package-level contracts and a small AST checker for module-public, composition-root, fixture, and empty-scope assertions. TypeScript uses Dependency Cruiser for graph checks plus a repository wrapper that rejects an empty scope. pnpm workspace cycles are disabled.

## Retained proof fixtures

`tests/architecture-fixtures` contains both allowed and forbidden dependency graphs. CI requires the allowed fixtures to pass and the forbidden fixtures to fail for the intended rules. This proves that a successful production-source check is not caused by an inactive or empty test scope.

## Local execution

From the repository root:

```text
uv sync --project backend --locked --group dev
uv run --project backend pytest backend/tests/architecture
PYTHONPATH=backend/src uv run --project backend lint-imports --config backend/.importlinter
corepack pnpm install --frozen-lockfile
corepack pnpm architecture
```

Pinned baseline: Python 3.12, uv 0.12.20, Import Linter 2.15, pytest 9.1.1, Node.js 24.19.0, pnpm 12.8.1, TypeScript 6.0.3, and Dependency Cruiser 18.4.0. TypeScript 6.0.3 is selected because Dependency Cruiser 18.4.0 declares support for TypeScript versions below 7.

## Exceptions

There are no initial exceptions. A future exception requires a stable rule ID, reason, owner, expiry, removal workorder, and approval. Broad path exclusions and silent warnings are not accepted.
