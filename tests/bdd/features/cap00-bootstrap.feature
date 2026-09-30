@CAP-00 @bootstrap
Feature: Verifiable bootstrap candidate
  The engineering team needs proof that the product foundation can be built,
  deployed manually, diagnosed, and recovered before business capabilities start.

  @BDD-CAP00-001
  Scenario: Healthy immutable candidate
    Given one candidate was built from a clean commit
    When the unchanged API, worker, and web images are started in isolated local staging
    Then every service reports the same commit and environment marker
    And no business operation is exposed

  @BDD-CAP00-002
  Scenario: Controlled unhealthy candidate recovery
    Given a known healthy CAP-00 candidate is recorded
    When the worker is started in the controlled not-ready mode
    Then staging rejects the candidate as unhealthy
    When the operator restores the known healthy candidate
    Then all services report healthy without changing the candidate identity
