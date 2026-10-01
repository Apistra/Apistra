# Python Code Conventions

Version: 1.0
Status: DECIDED
Owner: Apistra maintainers
Applies to: `backend/src`, `engineering`, and `tools`

## 1. Normative baseline

Apistra adopts the following sources in descending order of precedence:

1. this Apistra profile;
2. the Google Python Style Guide;
3. PEP 8 for Python code style;
4. PEP 257 for docstrings.

The repository configuration is the executable interpretation of this profile. A tool
upgrade or rule-set change requires a reviewed pull request and updated positive and
negative fixtures. Apistra uses Python 3.12, a line length of 100, double-quoted strings,
four-space indentation, and English identifiers, comments, docstrings, log messages, and
operator-facing error messages.

## 2. Naming and constants

- Modules, functions, methods, parameters, and variables use `snake_case`.
- Classes, exceptions, and type aliases use `CapWords`.
- Module and class constants use `UPPER_SNAKE_CASE`; non-public constants start with one
  underscore.
- Constants explain a role, not merely a value. `MAXIMUM_PROJECT_NAME_LENGTH` is valid;
  `NUMBER_128` is not.
- Stable finite contract values use `Enum` or `StrEnum` when they form a domain type.
- A constant that is part of a typed public module contract uses `Final` where practical.

A named constant, enum, message catalogue entry, or configuration value is mandatory for:

- domain statuses, roles, event types, error codes, protocol values, HTTP header names,
  media types, external field names, and persistence discriminators;
- security parameters, timeouts, retry limits, size limits, thresholds, and other values
  whose meaning is not obvious from the local expression;
- any non-documentation string used more than three times in one module;
- any non-trivial number used directly in executable production, engineering, or tool code.

The following do not require extraction solely to satisfy a style preference:

- `None`, booleans, `0`, `1`, and other values explicitly allowed by the configured
  analyser;
- a one-use internal diagnostic or formatting fragment whose meaning is fully local;
- test data and assertions, where visible literal values improve the scenario; tests must
  still extract shared contract data when duplication obscures intent;
- docstrings and comments;
- values supplied through typed configuration instead of source code.

Secrets, credentials, deployment URLs, and environment-specific values must never be
represented as source constants.

## 3. Types and public contracts

- All product functions and methods have complete parameter and return annotations.
- `Any` is prohibited in product contracts unless an external untyped boundary makes it
  unavoidable and the boundary immediately validates or converts the value.
- `object`, a protocol, a typed mapping, a dataclass, or a domain DTO is preferred over
  an unbounded dictionary.
- Nullable values are expressed explicitly with `T | None` and narrowed before use.
- Adapter implementations are assigned through their inward-facing port type.
- `cast`, `type: ignore`, and `noqa` are last-resort boundary tools. Every suppression names
  an exact rule and contains a short reason. Blanket suppressions are forbidden.
- Mypy strict mode is the type-correctness gate for `backend/src/apistra`.

## 4. Functions and control flow

- A function performs one coherent task and has a descriptive verb-led name.
- Cyclomatic complexity remains at most 10 under CI-TS-17.
- Parsing, validation, state transition, I/O, and presentation are separated when combining
  them would hide failure behavior.
- Boolean flag parameters are avoided in public APIs; use separate operations or an enum
  when the flag changes behavior materially.
- Mutable default arguments, wildcard imports, hidden import-time work, and broad exception
  catches are prohibited.
- Exceptions preserve their cause with `raise ... from ...` when translating a lower-level
  failure.

## 5. Errors, logging, and user-visible text

- Domain/application failures use stable error codes and typed error objects.
- Transport adapters translate typed failures to protocol responses; they do not invent
  business decisions.
- Public error details must be safe, stable, and free of credentials, tokens, SQL, stack
  traces, and internal identifiers.
- Logs are structured and use stable event names. Dynamic values are fields, not embedded
  into an unstructured message.
- User-interface copy belongs to the web localisation/message layer. Backend constants are
  not a substitute for localisation.

## 6. Imports, modules, and dependencies

- Imports are absolute, grouped, sorted, and located at module scope except where a
  documented runtime boundary requires otherwise.
- Product modules obey the existing ARCH dependency rules. A style refactor must not move
  ownership or create a new cross-module dependency.
- Vendor, transport, persistence, and framework types remain inside their adapters or
  entrypoints.
- New dependencies must be pinned in the lockfile and justified by a capability not already
  provided by the standard library or the approved toolchain.

## 7. Documentation and comments

- Public modules, classes, and non-obvious public functions use PEP 257 docstrings.
- Comments explain intent, constraints, or safety reasoning; they do not restate syntax.
- A TODO contains an issue or workorder reference. Unowned TODO/FIXME markers are forbidden.
- Code examples in documentation must follow the same formatter and naming rules where the
  tooling supports them.

## 8. Automated enforcement

CI-TS-18 is fail-closed and runs on every Python, lint, dependency, convention-document, or
CI change. It executes:

1. the configured Ruff lint families and Ruff formatter check;
2. Ruff `ANN` checks over `backend/src` for complete product annotations;
3. mypy strict mode over `backend/src/apistra`;
4. `wemake-python-styleguide` rules WPS226 and WPS432 over product, engineering, and tool
   code, excluding test suites as specified above;
5. retained positive and negative fixtures proving that compliant constants pass, an
   overused string fails with WPS226, and a magic number fails with WPS432;
6. a scan that rejects blanket `# noqa`, `# type: ignore`, and linter-disable directives.

No legacy baseline, per-module threshold increase, or local suppression may make a new
violation pass. A justified exception requires a separate reviewed rule change, a bounded
scope, an owner, an expiry or removal workorder, and retained evidence; it remains visible
as an exception rather than ordinary conformance.

## 9. Sources

- Google Python Style Guide: <https://google.github.io/styleguide/pyguide.html>
- PEP 8: <https://peps.python.org/pep-0008/>
- PEP 257: <https://peps.python.org/pep-0257/>
- Ruff rule catalogue: <https://docs.astral.sh/ruff/rules/>
- Mypy documentation: <https://mypy.readthedocs.io/>
- wemake-python-styleguide violations: <https://wemake-python-styleguide.readthedocs.io/en/latest/pages/usage/violations/index.html>
