@CAP-02 @PRC-01
Feature: Safe project-scoped AI configuration
  An Administrator needs write-only secrets, credential-safe endpoints,
  immutable agents, governed tools, and deterministic operating limits.

  Rule: Secret values never cross the protected write boundary

    @BDD-SECRET-001
    Scenario: Store and replace a project secret without disclosing its value
      Given fixture "FX-PRC-01-CAP02-CATALOG" is applied to isolated local staging
      And Administrator "admin.alpha" is authenticated through a protected session reference
      When Administrator "admin.alpha" stores secret "provider-primary" from protected parameter "CAP02_TEST_SECRET_PRIMARY"
      Then the response contains only the opaque project-scoped secret reference
      And the secret canary is absent from API responses, logs, exports, audit data, and evidence
      When Administrator "admin.alpha" replaces secret "provider-primary" from protected parameter "CAP02_TEST_SECRET_ROTATED"
      Then a new secret version is active without disclosing either value
      And a foreign-project, revoked, tampered, or unresolved reference is rejected without existence disclosure

  Rule: Endpoint probes validate destination policy before credential resolution

    @BDD-ENDPOINT-001
    Scenario: Save offline and execute one bounded credential-safe connection probe
      Given fixture "FX-PRC-01-CAP02-ENDPOINTS" is applied to isolated local staging
      And endpoint "local-llm" references secret "provider-primary" in project "Atlas Research"
      When Administrator "admin.alpha" saves endpoint "local-llm"
      Then no network request or credential resolution occurs
      When Administrator "admin.alpha" explicitly tests endpoint "local-llm"
      Then exactly one read-only provider probe uses the configured timeout and response-size bounds
      And only a normalised connection outcome is returned
      When the destination redirects, rebinds, or resolves to a forbidden metadata address
      Then the probe returns "Destination blocked" before credential resolution

  Rule: Agent publications retain exact configuration references

    @BDD-AGENT-001
    Scenario: Create an immutable agent version with explicit endpoint fallback
      Given fixture "FX-PRC-01-CAP02-CATALOG" is applied to isolated local staging
      When Administrator "admin.alpha" creates version 1 of agent "Research Analyst"
      Then the version retains the exact primary endpoint, fallback endpoint, tool-set, and limits-policy versions
      And the published agent version is read-only
      When a referenced catalogue display name changes
      Then agent version 1 retains its original identifiers and versions
      And editing agent version 1 creates a new draft rather than mutating it

  Rule: Tool effects and policies cannot bypass approval

    @BDD-TOOL-001
    Scenario: Enforce the active approval policy for protected tool effects
      Given fixture "FX-PRC-01-CAP02-POLICIES" is applied to isolated local staging
      And tool "research-readonly" is classified "READ"
      And tool "document-write" is classified "WRITE"
      When the active policy evaluates "research-readonly" action "search"
      Then the read action is permitted without approval
      When the active policy evaluates "document-write" action "replace"
      Then approval is required by default
      And a missing, expired, broader, or differently versioned exception does not grant approval
      And a timeout never changes the decision to approved

  Rule: Limits are deterministic at exact boundaries

    @BDD-LIMIT-001
    Scenario Outline: Evaluate a hard limit below, at, and above its configured value
      Given fixture "FX-PRC-01-CAP02-POLICIES" is applied to isolated local staging
      And policy "interactive-default@4" configures <limit> as <configured>
      When a run requests <observed> for <limit>
      Then the decision is <decision>
      And the decision records the exact policy version, boundary, result, actor, project, timestamp, and correlation ID
      And denial produces no protected side effect

      Examples:
        | limit               | configured | observed | decision |
        | maximum calls       | 10         | 9        | ALLOW    |
        | maximum calls       | 10         | 10       | ALLOW    |
        | maximum calls       | 10         | 11       | DENY     |
        | maximum concurrency | 2          | 3        | DENY     |
        | maximum cost        | 1.50 EUR   | 1.51 EUR | DENY     |
