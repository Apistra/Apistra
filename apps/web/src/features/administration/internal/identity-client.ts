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
