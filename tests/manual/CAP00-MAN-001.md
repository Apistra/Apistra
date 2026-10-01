# CAP00-MAN-001 — Manual immutable bootstrap acceptance

Purpose: independently confirm that the exact CAP-00 candidate can be deployed and recovered without an automatic branch deployment.

Preconditions: Docker is healthy; the candidate manifest and OCI archives exist; no production or foreign data is in scope; ports selected for the isolated project are unused.

1. Record the candidate manifest SHA-256 and the three image archive SHA-256 values. Expected: all four values are present and valid SHA-256 values.
2. Run the staging deployment command with a unique run identifier. Expected: a distinct Compose project, network, volume names, ports, and generated local credential reference are shown.
3. Read web `/api/health`, API `/health/live`, API `/health/ready`, and the worker health state. Expected: all report healthy and the same commit/environment marker; no secret value is returned.
4. Request an undefined API business route. Expected: `404`; CAP-00 exposes no business operation.
5. Capture a request correlation ID and locate the matching API log entry. Expected: the entry contains method, path, status, duration, and correlation ID but no credentials.
6. Run the controlled recovery test. Expected: the deliberately unhealthy worker is rejected, the known candidate is restored, and health returns without rebuilding images.
7. Stop and clean up the isolated environment. Expected: only resources with this run identifier are removed; unrelated Docker resources remain.

Record: operator, UTC start/end, candidate manifest SHA-256, run identifier, result for every step, deviations, and final ACCEPTED or REJECTED decision.
