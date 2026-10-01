# Apistra

Apistra is a platform for building, testing, publishing, and operating AI-assisted business processes that can be exposed through reliable, versioned APIs.

## Status

Early-stage build-in-public project. CAP-00 provides a health-only web/API/worker walking skeleton, executable architecture and behavioural tests, pinned container packaging, an isolated manual local-staging path, controlled recovery, and a lossless Softwaretest.it reporting adapter. Business capabilities have not started and no production-ready release exists.

## Product direction

Apistra is intended for developers, AI engineers, and technical solution architects who need to combine:

- configurable cloud or on-premise AI endpoints;
- distributed knowledge and cited retrieval;
- trusted connectors and governed tools;
- visual and YAML or JSON workflow authoring;
- durable asynchronous execution;
- human approval;
- versioned Process APIs;
- local, on-premise, and offline operation.

## Planning baseline

The current BuildBySpec planning package starts at [docs/planning/README.md](docs/planning/README.md).

Granular product slices are maintained as [one file per capability](docs/capabilities/README.md) and [one execution contract per workorder](docs/workorders/README.md).

The planning documents describe intended behaviour and delivery gates. The current CAP-00 implementation is technical evidence, not a released product. Branch protection, independent review, explicit human acceptance, and the candidate-bound Softwaretest.it round-trip are recorded. CAP-00 is accepted; CAP-01 product implementation and production approval have not begun.

The operational test rules are defined in the [Test Concept](docs/testing/test-concept.md); the system test structure remains in the [Test Architecture](docs/planning/06-test-architecture.md).

## Versioning and changes

The authoritative development version is stored in [VERSION](VERSION). Version meaning and release rules are defined in [VERSIONING.md](VERSIONING.md), and curated changes are recorded in [CHANGELOG.md](CHANGELOG.md). Version `0.0.0` denotes the unreleased CAP-00 development baseline, not a product release.

## Architecture foundation

The initial monorepo layout, dependency rules, retained positive and negative fixtures, and CI integration are documented in [docs/architecture/testing.md](docs/architecture/testing.md).

## CAP-00 operator entry point

Build, staging, recovery, evidence, and cleanup commands are documented in [docs/operations/cap00-bootstrap.md](docs/operations/cap00-bootstrap.md). The complete test map is in [docs/testing/cap00-test-matrix.md](docs/testing/cap00-test-matrix.md).

## Licensing

Apistra is source available under the paths described in [LICENSE](LICENSE): PolyForm Noncommercial 1.0.0 for its permitted purposes, PolyForm Free Trial 1.0.0 for a company evaluation of fewer than 32 consecutive calendar days, or a separately signed [Apistra Commercial License](COMMERCIAL-LICENSE.md). Apistra is not represented as OSI Open Source under this model. Earlier revisions retain their historical GNU AGPL version 3 grants; the exact boundary is recorded in [LICENSE-TRANSITION.md](LICENSE-TRANSITION.md).

## Contributions

The project is being developed in public, but external contributions are not accepted during the initial 0.x planning and foundation phase.
