import { describe, expect, it, vi } from "vitest";

import { bootstrapAdministrator, validateCredentials } from "./internal/identity-client";

describe("administrator bootstrap contract", () => {
  it("validates the server-owned credential boundaries before submission", () => {
    expect(validateCredentials({ username: "ad", password: "correct horse battery" })).toMatch(/3 to 128/);
    expect(validateCredentials({ username: "administrator", password: "too short" })).toMatch(/12 and 1024/);
    expect(validateCredentials({ username: "administrator", password: "correct horse battery" })).toBeNull();
  });

  it("posts only credentials to the same-origin versioned endpoint", async () => {
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      administrator: { id: "admin-id", username: "administrator" },
      csrf_token: "csrf",
      expires_at: "2026-10-02T00:00:00Z"
    }), { status: 201, headers: { "content-type": "application/json" } }));
    const receipt = await bootstrapAdministrator({ username: "administrator", password: "correct horse battery" }, request);
    expect(receipt.administrator.username).toBe("administrator");
    expect(request).toHaveBeenCalledWith(
      "/api/v1/administrators:bootstrap",
      expect.objectContaining({ method: "POST", credentials: "same-origin" })
    );
  });

  it("surfaces the safe server problem without transport internals", async () => {
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      title: "identity.bootstrap_closed",
      detail: "Administrator bootstrap is not available.",
      correlation_id: "corr"
    }), { status: 409, headers: { "content-type": "application/problem+json" } }));
    await expect(bootstrapAdministrator(
      { username: "administrator", password: "correct horse battery" }, request
    )).rejects.toThrow("Administrator bootstrap is not available.");
  });
});
