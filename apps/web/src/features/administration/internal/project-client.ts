import type { ProblemDetail } from "./identity-client";

export interface ProjectView {
  id: string;
  name: string;
  key: string;
  status: "ACTIVE" | "ARCHIVED";
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AuditEventView {
  id: string;
  event_type: string;
  created_at: string;
  correlation_id: string;
  actor: string | null;
  subject_id: string | null;
  installation_id?: string | null;
  project_id: string | null;
  project_key: string | null;
}

async function payload<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ProblemDetail;
  if (!response.ok) {
    throw new Error((body as ProblemDetail).detail || "The project request failed.");
  }
  return body as T;
}

export async function listProjects(request: typeof fetch = fetch): Promise<ProjectView[]> {
  const response = await request("/api/v1/projects", {
    credentials: "same-origin",
    cache: "no-store"
  });
  return (await payload<{ items: ProjectView[] }>(response)).items;
}

export async function createProject(
  input: { name: string; key: string },
  csrfToken: string,
  idempotencyKey: string,
  request: typeof fetch = fetch
): Promise<ProjectView> {
  return payload(await request("/api/v1/projects", {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "content-type": "application/json",
      "x-csrf-token": csrfToken,
      "idempotency-key": idempotencyKey
    },
    body: JSON.stringify(input)
  }));
}

export async function listAuditEvents(
  request: typeof fetch = fetch
): Promise<AuditEventView[]> {
  const response = await request("/api/v1/audit-events", {
    credentials: "same-origin",
    cache: "no-store"
  });
  return (await payload<{ items: AuditEventView[] }>(response)).items;
}
