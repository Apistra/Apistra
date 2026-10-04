import type { ProblemDetail } from "../../administration/public";

export interface VersionReference { id: string; version: number }
export interface AgentVersionInput {
  name: string;
  instructions: string;
  primary_endpoint: VersionReference;
  fallback_endpoint: VersionReference | null;
  tool_versions: VersionReference[];
  limits_policy_version: VersionReference | null;
}
export interface AgentVersionView extends AgentVersionInput {
  agent_id: string;
  project_id: string;
  version: number;
  status: "DRAFT" | "PUBLISHED";
  created_at: string;
  created_by: string;
}

async function payload<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ProblemDetail;
  if (!response.ok) throw new Error((body as ProblemDetail).detail || "Agent request failed.");
  return body as T;
}

export async function listAgents(projectId: string, request: typeof fetch = fetch) {
  const response = await request(`/api/v1/projects/${projectId}/agents`, {
    credentials: "same-origin", cache: "no-store"
  });
  return (await payload<{ items: AgentVersionView[] }>(response)).items;
}

export async function createAgent(
  projectId: string,
  input: AgentVersionInput,
  csrfToken: string,
  idempotencyKey: string,
  request: typeof fetch = fetch
) {
  return payload<AgentVersionView>(await request(`/api/v1/projects/${projectId}/agents`, {
    method: "POST", credentials: "same-origin",
    headers: { "content-type": "application/json", "x-csrf-token": csrfToken, "idempotency-key": idempotencyKey },
    body: JSON.stringify(input)
  }));
}
