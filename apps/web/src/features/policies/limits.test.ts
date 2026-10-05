import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import {
  createLimitPolicy,
  evaluateLimitPolicy,
  listLimitPolicies,
  type LimitPolicyInput
} from "./internal/limit-client";

const input: LimitPolicyInput = {
  name: "interactive-default",
  maximum_duration_seconds: 300,
  maximum_calls: 10,
  maximum_tokens: 20000,
  maximum_cost_minor_units: 150,
  currency: "EUR",
  maximum_concurrency: 2,
  rate_limit_requests: 30,
  rate_limit_window_seconds: 60,
  warning_threshold_percent: null
};

describe("resource limit policy boundary", () => {
  it("creates exact versioned policies and submits a deterministic observation", async () => {
    const policy = {
      ...input, policy_id: "policy-id", project_id: "project-id", version: 1,
      status: "PUBLISHED", created_at: "2026-10-05T10:00:00Z", created_by: "admin-id"
    } as const;
    const decision = {
      decision: "DENY", action: "STOP", policy_id: "policy-id", policy_version: 1,
      violated_limits: ["maximum_calls"], warned_limits: [], effect_permitted: false
    } as const;
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [policy] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(policy), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(decision)));
    expect((await listLimitPolicies("project-id", request))[0]).toEqual(policy);
    expect(await createLimitPolicy("project-id", input, "csrf", "key", request)).toEqual(policy);
    expect(request).toHaveBeenNthCalledWith(2,
      "/api/v1/projects/project-id/policies/limits",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "idempotency-key": "key" })
      })
    );
    expect((await evaluateLimitPolicy("project-id", "policy-id", 1, {
      duration_seconds: 0, calls: 11, tokens: 0, cost_minor_units: 0,
      concurrency: 0, requests_in_window: 0, rate_window_seconds: 60
    }, "csrf", request)).effect_permitted).toBe(false);
  });

  it("sends the observed version and preserves input in the editor on a conflict", async () => {
    const policy = {
      ...input, policy_id: "policy-id", project_id: "project-id", version: 4,
      status: "DRAFT", created_at: "2026-10-05T10:00:00Z", created_by: "admin-id"
    } as const;
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      detail: "This draft changed elsewhere. Reload the latest version before saving."
    }), { status: 409 }));
    await expect(createLimitPolicy("project-id", { ...input, maximum_calls: 12 }, "csrf", "key", request, policy))
      .rejects.toThrow("This draft changed elsewhere");
    expect(request).toHaveBeenCalledWith(
      "/api/v1/projects/project-id/policies/limits/policy-id/versions",
      expect.objectContaining({
        headers: expect.objectContaining({ "if-match": '"4"' }),
        body: expect.stringContaining('"maximum_calls":12')
      })
    );
    const source = readFileSync(new URL("./limits.tsx", import.meta.url), "utf8");
    expect(source).toContain("setError(caught instanceof Error ? caught.message");
    expect(source).toContain("Your input is retained for comparison.");
    for (const label of ["Limits and policies", "Create policy version", "Save policy draft", "Maximum cost", "Maximum concurrency", "Rate limit"]) {
      expect(source).toContain(label);
    }
  });
});
