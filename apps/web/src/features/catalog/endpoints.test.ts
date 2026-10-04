import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import {
  listEndpoints,
  storeEndpoint,
  testEndpoint,
  type EndpointView
} from "./internal/endpoint-client";

const endpoint: EndpointView = {
  id: "endpoint-id",
  project_id: "project-id",
  name: "local-llm",
  purpose: "GENERATIVE",
  provider_protocol: "OPENAI_COMPATIBLE",
  base_url: "http://127.0.0.1:18080/v1",
  model_identifier: "synthetic-chat",
  secret_reference_id: "secret-id",
  network_profile: "LOCAL",
  status: "UNVERIFIED",
  version: 1,
  last_probe_outcome: null,
  created_at: "2026-10-04T18:00:00Z",
  updated_at: "2026-10-04T18:00:00Z"
};

describe("endpoint catalogue boundary", () => {
  it("saves offline and tests through separate versioned operations", async () => {
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [endpoint] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(endpoint), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ...endpoint,
        version: 2,
        status: "VERIFIED",
        last_probe_outcome: "CONNECTION_VERIFIED"
      })));
    expect((await listEndpoints("project-id", request))[0]).toEqual(endpoint);
    await storeEndpoint(
      "project-id",
      {
        name: endpoint.name,
        purpose: endpoint.purpose,
        provider_protocol: endpoint.provider_protocol,
        base_url: endpoint.base_url,
        model_identifier: endpoint.model_identifier,
        secret_reference_id: endpoint.secret_reference_id,
        network_profile: endpoint.network_profile
      },
      "csrf",
      "idempotency",
      request
    );
    await testEndpoint(endpoint, "csrf", request);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/projects/project-id/endpoints/endpoint-id:test",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "if-match": '"1"' })
      })
    );
  });

  it("contains every approved DSN-005 field and normalized outcome", () => {
    const source = readFileSync(new URL("./endpoints.tsx", import.meta.url), "utf8");
    for (const label of [
      "Model endpoints",
      "Add endpoint",
      "Purpose",
      "Provider protocol",
      "Base URL",
      "Model identifier",
      "Secret reference",
      "Network profile",
      "Test connection",
      "Connection verified",
      "Connection failed",
      "Destination blocked",
      "Authentication failed",
      "Timed out",
      "Probe not supported"
    ]) {
      expect(source).toContain(label);
    }
    expect(source).toContain("Saving is offline");
    expect(source).toContain("Testing…");
  });
});
