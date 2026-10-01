import { describe, expect, it, vi } from "vitest";

import {
  bootstrapAdministrator,
  currentSession,
  installationStatus,
  signIn,
  signOut,
  validateCredentials
} from "./internal/identity-client";

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

  it("uses the same-origin session contract for sign-in, lookup, and revocation", async () => {
    const receipt = {
      administrator: { id: "admin-id", username: "administrator" },
      csrf_token: "csrf",
      expires_at: "2026-10-02T00:00:00Z"
    };
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(receipt), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(receipt), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    expect((await signIn({ username: "administrator", password: "correct horse battery" }, request)).csrf_token).toBe("csrf");
    expect((await currentSession(request))?.administrator.username).toBe("administrator");
    await expect(signOut("csrf", request)).resolves.toBeUndefined();
    expect(request).toHaveBeenLastCalledWith("/api/v1/session", expect.objectContaining({
      method: "DELETE",
      headers: { "x-csrf-token": "csrf" }
    }));
  });

  it("handles installation, logged-out, and safe session error responses", async () => {
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ bootstrap_available: true })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "signed out" }), { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        title: "identity.invalid_credentials",
        detail: "The username or password is invalid.",
        correlation_id: "corr"
      }), { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        title: "identity.csrf_invalid",
        detail: "The request could not be verified.",
        correlation_id: "corr"
      }), { status: 403 }));
    expect((await installationStatus(request)).bootstrap_available).toBe(true);
    expect(await currentSession(request)).toBeNull();
    await expect(signIn(
      { username: "administrator", password: "incorrect credential" }, request
    )).rejects.toThrow("The username or password is invalid.");
    await expect(signOut("wrong", request)).rejects.toThrow("The request could not be verified.");
  });
});
