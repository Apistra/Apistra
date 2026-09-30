# CAP-00 security baseline

CAP-00 has no authentication or business operation. Those controls start in CAP-01 and must not be simulated by the bootstrap shell.

Implemented controls:

- exact dependency lockfiles and runtime/tool pins;
- digest-pinned Python and Node base images;
- non-root UID/GID 10001 containers;
- read-only roots, bounded tmpfs, dropped capabilities, `no-new-privileges`, CPU/memory/PID limits;
- loopback-only published ports and a separate internal worker network;
- safe response headers and no-store health responses;
- correlation IDs and structured logs without request bodies or credentials;
- secret-pattern scan with a retained known-secret fixture;
- dependency vulnerability audits;
- SPDX SBOM and candidate/archive checksums;
- synthetic `.invalid` identities and credential references rather than secret values;
- safe-by-default dry-run external reporting and recursive redaction.
- live branch protection for `test`, `staging`, and `main`, including strict required checks, pull requests, linear history, resolved conversations, administrator enforcement, and force-push/deletion prevention.

Open risks and gates:

- Required approving and CODEOWNERS reviews remain disabled while only one qualified maintainer exists; enable them when independent maintainers are available.
- Softwaretest.it authentication, scopes, project/cycle binding, and write/read round-trip need authorised protected credentials.
- Commercial terms still require a signed agreement; no certification or production warranty exists.
- A qualified independent implementation/security review and human bootstrap acceptance remain pending.
- No production environment or production deployment process is defined.
