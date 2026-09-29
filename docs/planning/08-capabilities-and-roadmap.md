# Capabilities and Gate-Based Roadmap

Version: 0.2-draft
Status: DRAFT

## Control summary

**Result:** Apistra is split into nineteen vertically testable capabilities with one canonical contract per file and a gate-based release order.
**Change:** The former catalogue summaries are now indexed to detailed files under `docs/capabilities/`; no implementation or acceptance is inferred.
**Current position:** CAP-00 is implemented and hosted-verified but still awaits its external and human gates. CAP-01 through CAP-18 remain DRAFT.
**Main blocker:** Business implementation remains blocked by GATE-CAP00-DONE and Softwaretest.it publishing readiness.
**Next step:** Close CAP-00, then independently review and approve the next capability and only its first one or two workorders.

The roadmap has no dates. Progress depends on evidence gates, not elapsed time. The [capability catalogue](../capabilities/README.md) is canonical for capability scope, rules, acceptance, tests, dependencies, decisions, and workorder links.

## Release 0.0 — Delivery foundation

- [CAP-00 — Reproducible Delivery Walking Skeleton](../capabilities/CAP-00-reproducible-delivery-walking-skeleton.md)

Gate: complete bootstrap matrix on the exact candidate, isolated local staging, recovery, authenticated Softwaretest.it round-trip, independent review, and human bootstrap acceptance.

## Release 0.1 — Governed end-to-end AI process

- [CAP-01 — Installation and Isolated Project Administration](../capabilities/CAP-01-installation-and-isolated-project-administration.md)
- [CAP-02 — Secrets, Endpoints, Agents, Tools, and Limits](../capabilities/CAP-02-secrets-endpoints-agents-tools-and-limits.md)
- [CAP-03 — Connector Foundation and Trusted Sources](../capabilities/CAP-03-connector-foundation-and-trusted-sources.md)
- [CAP-04 — Knowledge and Cited Retrieval](../capabilities/CAP-04-knowledge-and-cited-retrieval.md)
- [CAP-05 — Workflow Authoring and Publication](../capabilities/CAP-05-workflow-authoring-and-publication.md)
- [CAP-06 — Durable Process API](../capabilities/CAP-06-durable-process-api.md)
- [CAP-07 — Human Approval and Controlled Writes](../capabilities/CAP-07-human-approval-and-controlled-writes.md)

Release gate: CAP-00 through CAP-07 accepted; offline demonstration and all required manual process packages pass; all automated results are confirmed in Softwaretest.it; no blocking architecture/security finding; legal, documentation, and brand gates pass.

## Release 0.2 — Advanced orchestration and integrations

- [CAP-08 — Advanced Control Flow](../capabilities/CAP-08-advanced-control-flow.md)
- [CAP-09 — Scheduled and Event-Triggered Execution](../capabilities/CAP-09-scheduled-and-event-triggered-execution.md)
- [CAP-10 — Expanded Connector Catalogue](../capabilities/CAP-10-expanded-connector-catalogue.md)
- [CAP-11 — Import, Export, and Templates](../capabilities/CAP-11-import-export-and-templates.md)

Release gate: advanced recovery/compensation, connector security and incremental sync, import/export isolation, and the unchanged-candidate 0.1 regression gate pass.

## Release 0.3 — Evaluation and AI quality

- [CAP-12 — Versioned Evaluation Datasets](../capabilities/CAP-12-versioned-evaluation-datasets.md)
- [CAP-13 — Evaluation Gates](../capabilities/CAP-13-evaluation-gates.md)
- [CAP-14 — Candidate Comparison](../capabilities/CAP-14-candidate-comparison.md)

Release gate: dataset provenance, judge calibration/limitations, non-AI sole authority, and reproducible comparison/regression evidence pass.

## Later 0.x

- [CAP-15 — Role-Based Administration and Enterprise Identity](../capabilities/CAP-15-role-based-administration-and-enterprise-identity.md)
- [CAP-16 — Trusted Third-Party Plugin Execution](../capabilities/CAP-16-trusted-third-party-plugin-execution.md)
- [CAP-17 — Kubernetes Deployment Profile](../capabilities/CAP-17-kubernetes-deployment-profile.md)
- [CAP-18 — Commercial Operations and Optional Managed Service](../capabilities/CAP-18-commercial-operations-and-optional-managed-service.md)

## Cross-capability gate rules

- One active capability and one or two independent active workorders are the default until review capacity is demonstrated.
- Blocked work and waiting reviews count as work in progress.
- Every capability ends with one final staging-acceptance workorder.
- Changes to shared foundations trigger explicit impact/invalidity analysis.
- No capability is accepted from partial green evidence, a percentage score, a merge, or an agent assertion.
- Workorder DONE, capability acceptance, release approval, and production approval are separate states.
