import type { ProblemDetail } from "../../administration/public";

export type EndpointPurpose = "GENERATIVE" | "EMBEDDING";
export type NetworkProfile = "CLOUD" | "ON_PREMISE" | "LOCAL";
export type ProbeOutcome =
  | "CONNECTION_VERIFIED"
  | "CONNECTION_FAILED"
  | "DESTINATION_BLOCKED"
  | "AUTHENTICATION_FAILED"
  | "TIMED_OUT"
  | "PROBE_NOT_SUPPORTED";

export interface EndpointView {
  id: string;
  project_id: string;
  name: string;
  purpose: EndpointPurpose;
  provider_protocol: "OPENAI_COMPATIBLE";
  base_url: string;
  model_identifier: string;
  secret_reference_id: string;
  network_profile: NetworkProfile;
  status: "UNVERIFIED" | "VERIFIED";
  version: number;
  last_probe_outcome: ProbeOutcome | null;
  created_at: string;
  updated_at: string;
}

export interface EndpointInput {
  name: string;
  purpose: EndpointPurpose;
  provider_protocol: "OPENAI_COMPATIBLE";
  base_url: string;
  model_identifier: string;
  secret_reference_id: string;
  network_profile: NetworkProfile;
}

async function payload<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ProblemDetail;
  if (!response.ok) {
    throw new Error((body as ProblemDetail).detail || "The endpoint request failed.");
  }
  return body as T;
}

export async function listEndpoints(
  projectId: string,
  request: typeof fetch = fetch
): Promise<EndpointView[]> {
  const response = await request(`/api/v1/projects/${projectId}/endpoints`, {
    credentials: "same-origin",
    cache: "no-store"
  });
  return (await payload<{ items: EndpointView[] }>(response)).items;
}

export async function storeEndpoint(
  projectId: string,
  input: EndpointInput,
  csrfToken: string,
  idempotencyKey: string,
  request: typeof fetch = fetch
): Promise<EndpointView> {
  return payload(await request(`/api/v1/projects/${projectId}/endpoints`, {
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

export async function testEndpoint(
  endpoint: EndpointView,
  csrfToken: string,
  request: typeof fetch = fetch
): Promise<EndpointView> {
  return payload(await request(
    `/api/v1/projects/${endpoint.project_id}/endpoints/${endpoint.id}:test`,
    {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "x-csrf-token": csrfToken,
        "if-match": `"${endpoint.version}"`
      }
    }
  ));
}
