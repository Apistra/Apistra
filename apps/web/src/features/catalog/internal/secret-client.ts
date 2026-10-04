import type { ProblemDetail } from "../../administration/public";

export interface SecretReferenceView {
  id: string;
  project_id: string;
  name: string;
  purpose: string;
  status: "ACTIVE" | "REVOKED";
  version: number;
  envelope_version: number;
  created_at: string;
  updated_at: string;
}

async function payload<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ProblemDetail;
  if (!response.ok) {
    throw new Error((body as ProblemDetail).detail || "The secret request failed.");
  }
  return body as T;
}

export async function listSecrets(
  projectId: string,
  request: typeof fetch = fetch
): Promise<SecretReferenceView[]> {
  const response = await request(`/api/v1/projects/${projectId}/secrets`, {
    credentials: "same-origin",
    cache: "no-store"
  });
  return (await payload<{ items: SecretReferenceView[] }>(response)).items;
}

export async function storeSecret(
  projectId: string,
  input: { name: string; purpose: string; value: string },
  csrfToken: string,
  idempotencyKey: string,
  request: typeof fetch = fetch
): Promise<SecretReferenceView> {
  return payload(await request(`/api/v1/projects/${projectId}/secrets`, {
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

export async function replaceSecret(
  reference: SecretReferenceView,
  value: string,
  csrfToken: string,
  request: typeof fetch = fetch
): Promise<SecretReferenceView> {
  return payload(await request(
    `/api/v1/projects/${reference.project_id}/secrets/${reference.id}`,
    {
      method: "PUT",
      credentials: "same-origin",
      headers: {
        "content-type": "application/json",
        "x-csrf-token": csrfToken,
        "if-match": `"${reference.version}"`
      },
      body: JSON.stringify({ value })
    }
  ));
}
