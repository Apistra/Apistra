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

The planning documents describe intended behaviour and delivery gates. The current CAP-00 implementation is technical evidence, not a released product. The final CAP-00 gate still requires repository branch protection, an authorised Softwaretest.it round-trip, independent review, and explicit human acceptance.

## Architecture foundation

The initial monorepo layout, dependency rules, retained positive and negative fixtures, and CI integration are documented in [docs/architecture/testing.md](docs/architecture/testing.md).

## CAP-00 operator entry point

Build, staging, recovery, evidence, and cleanup commands are documented in [docs/operations/cap00-bootstrap.md](docs/operations/cap00-bootstrap.md). The complete test map is in [docs/testing/cap00-test-matrix.md](docs/testing/cap00-test-matrix.md).

## Licensing

The repository is offered under the [GNU Affero General Public License version 3](LICENSE). A separate commercial agreement is described in [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md); no commercial licence is granted without a signed agreement.

## Contributions

The project is being developed in public, but external contributions are not accepted during the initial 0.x planning and foundation phase.
