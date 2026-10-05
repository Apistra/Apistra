import type { ProblemDetail } from "../../administration/public";

export interface LimitPolicyInput {
  name: string;
  maximum_duration_seconds: number;
  maximum_calls: number;
  maximum_tokens: number;
  maximum_cost_minor_units: number;
  currency: string;
  maximum_concurrency: number;
  rate_limit_requests: number;
  rate_limit_window_seconds: number;
  warning_threshold_percent: number | null;
}

export interface LimitPolicyView extends LimitPolicyInput {
  policy_id: string;
  project_id: string;
  version: number;
  status: "DRAFT" | "PUBLISHED";
  created_at: string;
  created_by: string;
}

export interface LimitObservation {
  duration_seconds: number;
  calls: number;
  tokens: number;
  cost_minor_units: number;
  concurrency: number;
  requests_in_window: number;
  rate_window_seconds: number;
}

export interface LimitDecision {
  decision: "ALLOW" | "WARN" | "DENY";
  action: "ALLOW" | "WARN" | "STOP";
  policy_id: string;
  policy_version: number;
  violated_limits: string[];
  warned_limits: string[];
  effect_permitted: boolean;
}

async function payload<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ProblemDetail;
  if (!response.ok) throw new Error((body as ProblemDetail).detail || "Limit policy request failed.");
  return body as T;
}

export async function listLimitPolicies(projectId: string, request: typeof fetch = fetch) {
  const response = await request(`/api/v1/projects/${projectId}/policies/limits`, {
    credentials: "same-origin", cache: "no-store"
  });
  return (await payload<{ items: LimitPolicyView[] }>(response)).items;
}

export async function listLimitPolicyVersions(
  projectId: string, policyId: string, request: typeof fetch = fetch
) {
  const response = await request(
    `/api/v1/projects/${projectId}/policies/limits/${policyId}/versions`,
    { credentials: "same-origin", cache: "no-store" }
  );
  return (await payload<{ items: LimitPolicyView[] }>(response)).items;
}

export async function createLimitPolicy(
  projectId: string,
  input: LimitPolicyInput,
  csrf: string,
  idempotencyKey: string,
  request: typeof fetch = fetch,
  base?: LimitPolicyView
) {
  const path = base
    ? `/api/v1/projects/${projectId}/policies/limits/${base.policy_id}/versions`
    : `/api/v1/projects/${projectId}/policies/limits`;
  return payload<LimitPolicyView>(await request(path, {
    method: "POST", credentials: "same-origin",
    headers: {
      "content-type": "application/json",
      "x-csrf-token": csrf,
      "idempotency-key": idempotencyKey,
      ...(base ? { "if-match": `"${base.version}"` } : {})
    },
    body: JSON.stringify(input)
  }));
}

export async function evaluateLimitPolicy(
  projectId: string,
  policyId: string,
  version: number,
  observation: LimitObservation,
  csrf: string,
  request: typeof fetch = fetch
) {
  return payload<LimitDecision>(await request(
    `/api/v1/projects/${projectId}/policies/limits/${policyId}/versions/${version}:evaluate`,
    {
      method: "POST", credentials: "same-origin",
      headers: { "content-type": "application/json", "x-csrf-token": csrf },
      body: JSON.stringify(observation)
    }
  ));
}

export async function publishLimitPolicy(
  projectId: string,
  policyId: string,
  version: number,
  csrf: string,
  request: typeof fetch = fetch
) {
  return payload<LimitPolicyView>(await request(
    `/api/v1/projects/${projectId}/policies/limits/${policyId}/versions/${version}:publish`,
    { method: "POST", credentials: "same-origin", headers: { "x-csrf-token": csrf } }
  ));
}
