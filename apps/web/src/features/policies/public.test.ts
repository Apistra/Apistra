import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import { createTool, listTools, type ToolVersionInput } from "./internal/tool-client";

const schema = { $schema: "https://json-schema.org/draft/2020-12/schema", type: "object" };
const input: ToolVersionInput = {
  name: "document-write",
  description: "Replace a document.",
  input_schema: schema,
  output_schema: schema,
  effect_class: "WRITE",
  actions: ["replace"]
};

describe("governed tool boundary", () => {
  it("lists and creates exact versioned contracts", async () => {
    const created = {
      ...input,
      tool_id: "tool-id",
      project_id: "project-id",
      version: 1,
      status: "PUBLISHED",
      created_at: "2026-10-05T06:00:00Z",
      created_by: "administrator-id"
    } as const;
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [created] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(created), { status: 201 }));
    expect((await listTools("project-id", request))[0]).toEqual(created);
    expect(await createTool("project-id", input, "csrf", "key", request)).toEqual(created);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/projects/project-id/tools",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "idempotency-key": "key" })
      })
    );
  });

  it("contains every approved DSN-023 label and protected-effect warning", () => {
    const source = readFileSync(new URL("./public.tsx", import.meta.url), "utf8");
    for (const label of [
      "Tools", "Add tool", "Name", "Description", "Input schema",
      "Output schema", "Effect class", "Actions", "Limits &amp; Policies"
    ]) expect(source).toContain(label);
    expect(source).toContain("Approval required by default");
    expect(source).toContain("Administrative");
  });
});
