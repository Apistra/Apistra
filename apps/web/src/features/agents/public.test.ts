import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import { createAgent, listAgents, type AgentVersionInput } from "./internal/agent-client";

const input: AgentVersionInput = {
  name: "Research Analyst",
  instructions: "Use cited evidence.",
  primary_endpoint: { id: "primary-id", version: 2 },
  fallback_endpoint: { id: "fallback-id", version: 1 },
  tool_versions: [],
  limits_policy_version: null
};

describe("agent version boundary", () => {
  it("lists and creates exact version references", async () => {
    const created = {
      ...input,
      agent_id: "agent-id",
      project_id: "project-id",
      version: 1,
      status: "PUBLISHED",
      created_at: "2026-10-04T20:00:00Z",
      created_by: "administrator-id"
    } as const;
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [created] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(created), { status: 201 }));
    expect((await listAgents("project-id", request))[0]).toEqual(created);
    expect(await createAgent("project-id", input, "csrf", "key", request)).toEqual(created);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/projects/project-id/agents",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "idempotency-key": "key" })
      })
    );
  });

  it("contains every approved DSN-022 field and exact-reference summary", () => {
    const source = readFileSync(new URL("./public.tsx", import.meta.url), "utf8");
    for (const label of [
      "Agent versions",
      "Create agent version",
      "Agent name",
      "Instructions",
      "Primary endpoint",
      "Fallback endpoint (optional)",
      "Tool set",
      "Limits policy"
    ]) expect(source).toContain(label);
    expect(source).toContain("Published versions are read-only");
    expect(source).toContain("primary_endpoint.version");
    expect(source).toContain("fallback_endpoint.version");
  });
});
