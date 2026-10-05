import type { ProblemDetail } from "../../administration/public";

export type EffectClass = "READ" | "WRITE" | "ADMINISTRATIVE";
export interface ToolVersionInput {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  effect_class: EffectClass;
  actions: string[];
}
export interface ToolVersionView extends ToolVersionInput {
  tool_id: string;
  project_id: string;
  version: number;
  status: "DRAFT" | "PUBLISHED";
  created_at: string;
  created_by: string;
}

async function payload<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ProblemDetail;
  if (!response.ok) throw new Error((body as ProblemDetail).detail || "Tool request failed.");
  return body as T;
}

export async function listTools(projectId: string, request: typeof fetch = fetch) {
  const response = await request(`/api/v1/projects/${projectId}/tools`, {
    credentials: "same-origin", cache: "no-store"
  });
  return (await payload<{ items: ToolVersionView[] }>(response)).items;
}

export async function createTool(
  projectId: string,
  input: ToolVersionInput,
  csrfToken: string,
  idempotencyKey: string,
  request: typeof fetch = fetch
) {
  return payload<ToolVersionView>(await request(`/api/v1/projects/${projectId}/tools`, {
    method: "POST", credentials: "same-origin",
    headers: {
      "content-type": "application/json",
      "x-csrf-token": csrfToken,
      "idempotency-key": idempotencyKey
    },
    body: JSON.stringify(input)
  }));
}
