# Workorder Catalogue

Version: 0.7-draft
Status: DRAFT

Each file is one execution contract. A file is not implementation permission: its Status, prerequisites, expectation review, and gates remain binding.

Version 0.7 adds the separately gated Softwaretest.it Steering handover while preserving the version 0.6 execution contract. Every workorder has a delivery class, one owned verification group, explicit positive/negative/boundary oracles, expectation sources, counterexamples, and a dependency graph. Workorder numbers are stable identifiers, not execution order: the declared prerequisites govern readiness, and publication work may intentionally precede lower-numbered implementation work.

Only `DRAFT`, `BLOCKED`, `READY`, and `DONE` are valid workflow statuses. Implementation, evidence, and approval are recorded separately. Behavioural scenarios and manual package namespaces are governed by the [canonical test-ID catalogue](../testing/test-id-catalog.md); individual manual cases are allocated only by the owning publication workorder.

Every CAP-01 through CAP-18 workorder names literal paths from the [business repository path contract](../planning/12-repository-path-contract.md). `EXISTING` records the observed `be7e84d` location; `PLANNED` records an exact target below an approved root without claiming that it already exists. CAP-01 child paths are approved; later capability mappings remain subject to their READY review, including the CAP-16 and CAP-17 new-root blockers. An agent may not invent or use an unlisted repository path.

## CAP-00

- [WO-CAP-00-01 — Establish repository governance and planning checks](CAP-00/WO-CAP-00-01.md) — DONE; protected repository and hosted checks verified
- [WO-CAP-00-02 — Create the monorepo walking skeleton](CAP-00/WO-CAP-00-02.md) — DONE; complete revision 0.6 workflow verified
- [WO-CAP-00-03 — Package immutable container candidates](CAP-00/WO-CAP-00-03.md) — DONE; immutable candidate and external binding verified
- [WO-CAP-00-04 — Establish isolated local staging and recovery](CAP-00/WO-CAP-00-04.md) — DONE; staging, failure, and recovery verified
- [WO-CAP-00-05 — Establish Softwaretest.it publishing readiness](CAP-00/WO-CAP-00-05.md) — DONE; authenticated round-trip and receipts verified
- [WO-CAP-00-06 — Provide synthetic staging fixtures](CAP-00/WO-CAP-00-06.md) — DONE; fixture contracts and negative proofs verified
- [WO-CAP-00-07 — Complete bootstrap candidate gate](CAP-00/WO-CAP-00-07.md) — DONE; CAP-00 evidence and human acceptance package complete
- [WO-CAP-00-08 — Publish canonical Steering sources](CAP-00/WO-CAP-00-08.md) — DONE; authenticated import receipts, complete export readback, review, and product-owner approval recorded

## CAP-01

- [WO-CAP-01-01 — Implement local Administrator bootstrap and revocable session](CAP-01/WO-CAP-01-01.md) — DONE; implementation and technical review complete
- [WO-CAP-01-02 — Implement installation and isolated project lifecycle](CAP-01/WO-CAP-01-02.md) — DONE; implementation conformance and hosted evidence verified
- [WO-CAP-01-03 — Implement project-context enforcement and audit](CAP-01/WO-CAP-01-03.md) — DONE; implementation conformance and hosted evidence verified
- [WO-CAP-01-04 — Publish and verify PRC-01 test definitions](CAP-01/WO-CAP-01-04.md) — DONE; all six definitions published and read back
- [WO-CAP-01-05 — Accept CAP-01 on local staging](CAP-01/WO-CAP-01-05.md) — READY; fixture application and six manual executions remain

## CAP-02

- [WO-CAP-02-01 — Implement encrypted project secret references](CAP-02/WO-CAP-02-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-02-02 — Implement model and embedding endpoint catalogue](CAP-02/WO-CAP-02-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-02-03 — Implement versioned agents and explicit fallback](CAP-02/WO-CAP-02-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-02-04 — Implement governed tool contracts and approval classification](CAP-02/WO-CAP-02-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-02-05 — Implement configurable limits and budget decisions](CAP-02/WO-CAP-02-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-02-06 — Publish and verify CAP-02 test definitions](CAP-02/WO-CAP-02-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-02-07 — Accept CAP-02 on local staging](CAP-02/WO-CAP-02-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-03

- [WO-CAP-03-01 — Define connector SDK, capability manifest, and compliance kit](CAP-03/WO-CAP-03-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-03-02 — Implement file or directory connector](CAP-03/WO-CAP-03-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-03-03 — Implement REST connector with SSRF protections](CAP-03/WO-CAP-03-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-03-04 — Implement Git connector](CAP-03/WO-CAP-03-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-03-05 — Implement manual, scheduled, and incremental synchronisation contract](CAP-03/WO-CAP-03-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-03-06 — Publish and verify CAP-03 test definitions](CAP-03/WO-CAP-03-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-03-07 — Accept CAP-03 on local staging](CAP-03/WO-CAP-03-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-04

- [WO-CAP-04-01 — Implement canonical document and provenance model](CAP-04/WO-CAP-04-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-02 — Implement extraction, cleaning, metadata, and chunking pipeline](CAP-04/WO-CAP-04-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-03 — Implement versioned embedding configuration](CAP-04/WO-CAP-04-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-04 — Implement Qdrant adapter behind vector-store port](CAP-04/WO-CAP-04-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-05 — Implement cited retrieval](CAP-04/WO-CAP-04-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-06 — Implement update, deletion, and reconciliation](CAP-04/WO-CAP-04-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-07 — Publish and verify PRC-02 test definitions](CAP-04/WO-CAP-04-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-04-08 — Accept CAP-04 on local staging](CAP-04/WO-CAP-04-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-05

- [WO-CAP-05-01 — Define canonical versioned workflow schema](CAP-05/WO-CAP-05-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-02 — Implement graph and node validation](CAP-05/WO-CAP-05-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-03 — Review, refine, and approve visual design references](CAP-05/WO-CAP-05-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-04 — Implement visual workflow editor](CAP-05/WO-CAP-05-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-05 — Implement YAML and JSON editor with semantic round-trip](CAP-05/WO-CAP-05-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-06 — Implement draft lifecycle and conflict handling](CAP-05/WO-CAP-05-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-07 — Implement immutable publication](CAP-05/WO-CAP-05-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-08 — Publish and verify PRC-03 test definitions](CAP-05/WO-CAP-05-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-05-09 — Accept CAP-05 on local staging](CAP-05/WO-CAP-05-09.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-06

- [WO-CAP-06-01 — Select durable execution engine through approved ADR](CAP-06/WO-CAP-06-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-02 — Implement run and node-attempt state machines](CAP-06/WO-CAP-06-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-03 — Implement versioned Process API contracts](CAP-06/WO-CAP-06-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-04 — Implement start idempotency and project API keys](CAP-06/WO-CAP-06-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-05 — Implement durable node execution and checkpoints](CAP-06/WO-CAP-06-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-06 — Implement status, result, cancellation, and safe errors](CAP-06/WO-CAP-06-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-07 — Implement signed callbacks with retry](CAP-06/WO-CAP-06-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-08 — Implement run trace and operational visibility](CAP-06/WO-CAP-06-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-09 — Publish and verify PRC-04 test definitions](CAP-06/WO-CAP-06-09.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-06-10 — Accept CAP-06 on local staging](CAP-06/WO-CAP-06-10.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-07

- [WO-CAP-07-01 — Implement versioned write policy and default approval](CAP-07/WO-CAP-07-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-07-02 — Implement durable human-task state](CAP-07/WO-CAP-07-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-07-03 — Implement human-task inbox and decision UI](CAP-07/WO-CAP-07-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-07-04 — Implement approval API and audit](CAP-07/WO-CAP-07-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-07-05 — Implement rejection and non-executing timeout paths](CAP-07/WO-CAP-07-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-07-06 — Publish and verify PRC-05 test definitions](CAP-07/WO-CAP-07-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-07-07 — Accept CAP-07 on local staging](CAP-07/WO-CAP-07-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-08

- [WO-CAP-08-01 — Define canonical advanced-control-flow node contracts](CAP-08/WO-CAP-08-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-02 — Implement durable parallel and merge execution](CAP-08/WO-CAP-08-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-03 — Implement bounded loop and for-each execution](CAP-08/WO-CAP-08-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-04 — Implement versioned subflow invocation](CAP-08/WO-CAP-08-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-05 — Implement explicit fallback paths](CAP-08/WO-CAP-08-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-06 — Implement durable human input and human edit](CAP-08/WO-CAP-08-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-07 — Publish and verify PRC-08 test definitions](CAP-08/WO-CAP-08-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-08-08 — Accept CAP-08 on local staging](CAP-08/WO-CAP-08-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-09

- [WO-CAP-09-01 — Define versioned trigger model and policies](CAP-09/WO-CAP-09-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-09-02 — Implement scheduled workflow starts](CAP-09/WO-CAP-09-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-09-03 — Implement authenticated event ingress and replay protection](CAP-09/WO-CAP-09-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-09-04 — Implement pause, disable, missed-event, and bounded catch-up behavior](CAP-09/WO-CAP-09-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-09-05 — Publish and verify PRC-09 test definitions](CAP-09/WO-CAP-09-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-09-06 — Accept CAP-09 on local staging](CAP-09/WO-CAP-09-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-10

- [WO-CAP-10-01 — Extend connector compliance contract for remote enterprise sources](CAP-10/WO-CAP-10-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-02 — Implement S3-compatible storage connector](CAP-10/WO-CAP-10-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-03 — Implement PostgreSQL connector](CAP-10/WO-CAP-10-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-04 — Implement website connector](CAP-10/WO-CAP-10-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-05 — Implement Jira connector](CAP-10/WO-CAP-10-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-06 — Implement Confluence connector](CAP-10/WO-CAP-10-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-07 — Publish and verify expanded-connector test definitions](CAP-10/WO-CAP-10-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-10-08 — Accept CAP-10 on local staging](CAP-10/WO-CAP-10-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-11

- [WO-CAP-11-01 — Define export manifest and compatibility contract](CAP-11/WO-CAP-11-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-11-02 — Implement secret-free project export package](CAP-11/WO-CAP-11-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-11-03 — Implement import preview and mapping](CAP-11/WO-CAP-11-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-11-04 — Implement compatibility and conflict handling](CAP-11/WO-CAP-11-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-11-05 — Enforce import ownership and project isolation](CAP-11/WO-CAP-11-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-11-06 — Publish and verify PRC-10 test definitions](CAP-11/WO-CAP-11-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-11-07 — Accept CAP-11 on local staging](CAP-11/WO-CAP-11-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-12

- [WO-CAP-12-01 — Define evaluation dataset, case, and provenance schemas](CAP-12/WO-CAP-12-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-12-02 — Implement dataset draft and immutable version lifecycle](CAP-12/WO-CAP-12-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-12-03 — Implement safe dataset import and validation](CAP-12/WO-CAP-12-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-12-04 — Implement deterministic evaluation runner and result model](CAP-12/WO-CAP-12-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-12-05 — Publish and verify evaluation-dataset test definitions](CAP-12/WO-CAP-12-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-12-06 — Accept CAP-12 on local staging](CAP-12/WO-CAP-12-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-13

- [WO-CAP-13-01 — Define versioned metric registry and evaluation policy](CAP-13/WO-CAP-13-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-13-02 — Implement deterministic evaluation gates](CAP-13/WO-CAP-13-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-13-03 — Implement observe, warn, review, and block actions](CAP-13/WO-CAP-13-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-13-04 — Calibrate AI-assisted judge and document limitations](CAP-13/WO-CAP-13-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-13-05 — Implement human evaluation review and audit](CAP-13/WO-CAP-13-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-13-06 — Publish and verify evaluation-gate test definitions](CAP-13/WO-CAP-13-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-13-07 — Accept CAP-13 on local staging](CAP-13/WO-CAP-13-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-14

- [WO-CAP-14-01 — Define comparable candidate snapshot contract](CAP-14/WO-CAP-14-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-14-02 — Implement controlled candidate comparison execution](CAP-14/WO-CAP-14-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-14-03 — Implement quality, latency, token, and cost aggregation](CAP-14/WO-CAP-14-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-14-04 — Implement reproducibility package and comparison export](CAP-14/WO-CAP-14-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-14-05 — Publish and verify candidate-comparison test definitions](CAP-14/WO-CAP-14-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-14-06 — Accept CAP-14 on local staging](CAP-14/WO-CAP-14-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-15

- [WO-CAP-15-01 — Define versioned role and permission model](CAP-15/WO-CAP-15-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-02 — Implement project membership lifecycle](CAP-15/WO-CAP-15-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-03 — Implement OIDC and SSO identity adapter](CAP-15/WO-CAP-15-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-04 — Implement account linking and enterprise session lifecycle](CAP-15/WO-CAP-15-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-05 — Implement revocation and privilege-change propagation](CAP-15/WO-CAP-15-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-06 — Implement separation-of-duties controls](CAP-15/WO-CAP-15-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-07 — Publish and verify PRC-11 test definitions](CAP-15/WO-CAP-15-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-15-08 — Accept CAP-15 on local staging](CAP-15/WO-CAP-15-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-16

- [WO-CAP-16-01 — Define signed plugin manifest and package contract](CAP-16/WO-CAP-16-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-02 — Define plugin permission and compatibility model](CAP-16/WO-CAP-16-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-03 — Implement trusted plugin installation and update](CAP-16/WO-CAP-16-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-04 — Implement isolated plugin execution](CAP-16/WO-CAP-16-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-05 — Implement plugin revocation and in-flight handling](CAP-16/WO-CAP-16-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-06 — Publish plugin SDK and compliance kit](CAP-16/WO-CAP-16-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-07 — Publish and verify PRC-12 test definitions](CAP-16/WO-CAP-16-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-16-08 — Accept CAP-16 on local staging](CAP-16/WO-CAP-16-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-17

- [WO-CAP-17-01 — Define supported Kubernetes topology and packaging](CAP-17/WO-CAP-17-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-17-02 — Implement external configuration, secrets, and storage contract](CAP-17/WO-CAP-17-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-17-03 — Implement Kubernetes health, observability, and diagnostics](CAP-17/WO-CAP-17-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-17-04 — Implement migration, upgrade, rollback, and restore](CAP-17/WO-CAP-17-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-17-05 — Implement Kubernetes security and hardening profile](CAP-17/WO-CAP-17-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-17-06 — Publish and verify PRC-13 test definitions](CAP-17/WO-CAP-17-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-17-07 — Accept CAP-17 on Kubernetes staging](CAP-17/WO-CAP-17-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

## CAP-18

- [WO-CAP-18-01 — Define commercial entitlement model](CAP-18/WO-CAP-18-01.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-02 — Implement signed offline licence verification](CAP-18/WO-CAP-18-02.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-03 — Implement licence administration and safe status reporting](CAP-18/WO-CAP-18-03.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-04 — Implement redacted support bundle export](CAP-18/WO-CAP-18-04.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-05 — Define managed-service responsibility and privacy boundaries](CAP-18/WO-CAP-18-05.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-06 — Define production environment and release contract](CAP-18/WO-CAP-18-06.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-07 — Complete legal and commercial operations documentation](CAP-18/WO-CAP-18-07.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-08 — Publish and verify PRC-14 test definitions](CAP-18/WO-CAP-18-08.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass
- [WO-CAP-18-09 — Accept CAP-18 on approved staging](CAP-18/WO-CAP-18-09.md) — DRAFT; blocked from implementation until CAP-00 and named prerequisites pass

