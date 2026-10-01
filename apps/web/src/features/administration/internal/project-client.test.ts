import { describe, expect, it, vi } from "vitest";

import { createProject, listAuditEvents, listProjects } from "./project-client";

const project = {
  id: "11111111-1111-4111-8111-111111111111",
  name: "Atlas Research",
  key: "ATLAS",
  status: "ACTIVE" as const,
  version: 1,
  created_at: "2026-10-01T12:00:00Z",
  updated_at: "2026-10-01T12:00:00Z"
};

describe("project administration client", () => {
  it("lists only the server-authorised project representation", async () => {
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [project] })));
    expect(await listProjects(request)).toEqual([project]);
    expect(request).toHaveBeenCalledWith("/api/v1/projects", expect.objectContaining({ credentials: "same-origin" }));
  });

  it("creates through the CSRF and idempotency contract", async () => {
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify(project), { status: 201 }));
    expect(await createProject({ name: project.name, key: project.key }, "csrf", "idem", request)).toEqual(project);
    expect(request).toHaveBeenCalledWith("/api/v1/projects", expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "x-csrf-token": "csrf", "idempotency-key": "idem" })
    }));
  });

  it("surfaces only the safe problem detail", async () => {
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      title: "project.key_conflict",
      detail: "Project key is already in use.",
      correlation_id: "corr"
    }), { status: 409 }));
    await expect(createProject({ name: project.name, key: project.key }, "csrf", "idem", request))
      .rejects.toThrow("Project key is already in use.");
  });

  it("reads the authenticated audit contract without mutation headers", async () => {
    const event = {
      id: "22222222-2222-4222-8222-222222222222",
      event_type: "project.created",
      created_at: "2026-10-01T12:00:00Z",
      correlation_id: "corr-owned-project",
      actor: "administrator",
      subject_id: project.id,
      project_id: project.id,
      project_key: project.key
    };
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [event] })));

    expect(await listAuditEvents(request)).toEqual([event]);
    expect(request).toHaveBeenCalledWith(
      "/api/v1/audit-events",
      expect.objectContaining({ credentials: "same-origin", cache: "no-store" })
    );
  });
});
