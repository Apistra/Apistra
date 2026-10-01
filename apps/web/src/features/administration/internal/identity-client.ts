export interface ProblemDetail {
  title: string;
  detail: string;
  correlation_id: string;
}

export interface SessionReceipt {
  administrator: { id: string; username: string };
  csrf_token: string;
  expires_at: string;
}

export interface Credentials {
  username: string;
  password: string;
}

export interface InstallationStatus {
  bootstrap_available: boolean;
}

export interface SessionView {
  administrator: { id: string; username: string };
  expires_at: string;
}

export function focusErrorAlert(element: { focus: () => void } | null): void {
  element?.focus();
}

export function validateCredentials(credentials: Credentials): string | null {
  if (!/^[A-Za-z0-9][A-Za-z0-9_.@-]{2,127}$/.test(credentials.username)) {
    return "Use 3 to 128 letters, numbers, or approved punctuation for the username.";
  }
  if (credentials.password.length < 12 || credentials.password.length > 1024) {
    return "Use a password between 12 and 1024 characters.";
  }
  return null;
}

export async function bootstrapAdministrator(
  credentials: Credentials,
  request: typeof fetch = fetch
): Promise<SessionReceipt> {
  const response = await request("/api/v1/administrators:bootstrap", {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(credentials)
  });
  const payload = (await response.json()) as SessionReceipt | ProblemDetail;
  if (!response.ok) {
    throw new Error((payload as ProblemDetail).detail || "Administrator creation failed.");
  }
  return payload as SessionReceipt;
}

async function readPayload<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as T | ProblemDetail;
  if (!response.ok) {
    throw new Error((payload as ProblemDetail).detail || "The request failed.");
  }
  return payload as T;
}

export async function installationStatus(
  request: typeof fetch = fetch
): Promise<InstallationStatus> {
  return readPayload(await request("/api/v1/installation", { cache: "no-store" }));
}

export async function currentSession(
  request: typeof fetch = fetch
): Promise<SessionView | null> {
  const response = await request("/api/v1/session", {
    credentials: "same-origin",
    cache: "no-store"
  });
  if (response.status === 401) return null;
  return readPayload(response);
}

export async function signIn(
  credentials: Credentials,
  request: typeof fetch = fetch
): Promise<SessionReceipt> {
  return readPayload(await request("/api/v1/sessions", {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(credentials)
  }));
}

export async function signOut(
  csrfToken: string,
  request: typeof fetch = fetch
): Promise<void> {
  const response = await request("/api/v1/session", {
    method: "DELETE",
    credentials: "same-origin",
    headers: { "x-csrf-token": csrfToken }
  });
  if (!response.ok) {
    const payload = (await response.json()) as ProblemDetail;
    throw new Error(payload.detail || "Sign out failed.");
  }
}
