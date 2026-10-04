import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import { listSecrets, replaceSecret, storeSecret } from "./internal/secret-client";

const reference = {
  id: "secret-id",
  project_id: "project-id",
  name: "provider-primary",
  purpose: "Primary endpoint",
  status: "ACTIVE" as const,
  version: 1,
  envelope_version: 1,
  created_at: "2026-10-04T12:00:00Z",
  updated_at: "2026-10-04T12:00:00Z"
};

describe("secret reference boundary", () => {
  it("uses same-origin authenticated requests and never expects readable values", async () => {
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [reference] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(reference), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...reference, version: 2 })));
    expect((await listSecrets("project-id", request))[0]).not.toHaveProperty("value");
    await storeSecret(
      "project-id",
      { name: "provider-primary", purpose: "Primary endpoint", value: "canary" },
      "csrf",
      "idempotency",
      request
    );
    await replaceSecret(reference, "rotated", "csrf", request);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/projects/project-id/secrets/secret-id",
      expect.objectContaining({ method: "PUT" })
    );
  });

  it("contains the approved DSN-006 labels and masked inputs", () => {
    const source = readFileSync(new URL("./public.tsx", import.meta.url), "utf8");
    for (const label of [
      "Secret references",
      "Add secret",
      "Name",
      "Purpose",
      "Secret value",
      "Store secret",
      "Replace value",
      "Secret stored. The value cannot be viewed again."
    ]) {
      expect(source).toContain(label);
    }
    expect(source).toContain('type="password"');
  });
});
