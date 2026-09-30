@CAP-01 @PRC-01
Feature: Offline installation administration and project isolation
  An Administrator needs a single local bootstrap, revocable authentication,
  and project operations that never disclose a foreign project.

  Rule: A local Administrator bootstrap is single-use and sessions are revocable

    @BDD-AUTH-001
    Scenario: Bootstrap one Administrator, authenticate, and revoke the session
      Given fixture "FX-PRC-01-FRESH" is applied to isolated local staging
      And no Administrator exists in the installation
      When the operator bootstraps Administrator "admin.alpha" with the protected password reference "STAGING_ADMIN_PASSWORD"
      Then exactly one Administrator account exists
      And audit event "administrator.bootstrap.completed" identifies Administrator "admin.alpha"
      When Administrator "admin.alpha" signs in with the protected password reference "STAGING_ADMIN_PASSWORD"
      Then an opaque revocable server-side session is established
      And the response discloses no password or session value
      When Administrator "admin.alpha" signs out
      Then audit event "session.revoked" identifies Administrator "admin.alpha"
      And reuse of the revoked session is rejected without project metadata
      When the operator repeats Administrator bootstrap for "admin.alpha"
      Then the request is rejected without creating another Administrator

  Rule: Project access is authorised by server-side project context

    @BDD-PROJ-001
    Scenario: Create an isolated project and deny a foreign project context
      Given fixture "FX-PRC-01-ADMIN-NO-PROJECT" is applied to isolated local staging
      And Administrator "admin.alpha" is authenticated through a protected session reference
      When Administrator "admin.alpha" creates project "Atlas Research" with project key "ATLAS"
      Then project "Atlas Research" is selected as the current authorised project
      And audit event "project.created" identifies Administrator "admin.alpha" and project "Atlas Research"
      When fixture "FX-PRC-01-ISOLATION" is applied to the same isolated local staging instance
      And Administrator "admin.alpha" requests project "22222222-2222-4222-8222-222222222222"
      Then the request is denied before foreign project data is read
      And the response is indistinguishable from an unknown project response
      And no name, key, owner, audit data, or other metadata of the foreign project is disclosed

  Rule: Fixture definitions do not imply execution evidence

    Scenario: Reject execution without a verified staging fixture receipt
      Given a CAP-01 fixture descriptor exists locally
      But no application receipt for the unchanged staging candidate exists
      When CAP-01 manual execution is requested
      Then execution remains blocked
      And no manual or BDD result is reported as passed
