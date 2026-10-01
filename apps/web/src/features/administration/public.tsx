"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import {
  bootstrapAdministrator,
  type Credentials,
  validateCredentials
} from "./internal/identity-client";

type State = "editing" | "submitting" | "created";

export function AdministratorBootstrap() {
  const [credentials, setCredentials] = useState<Credentials>({ username: "", password: "" });
  const [state, setState] = useState<State>("editing");
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validation = validateCredentials(credentials);
    if (validation) {
      setMessage(validation);
      return;
    }
    setState("submitting");
    setMessage(null);
    try {
      const receipt = await bootstrapAdministrator(credentials);
      setCredentials({ username: receipt.administrator.username, password: "" });
      setState("created");
      setMessage("Administrator created. The local session is active.");
    } catch (error) {
      setState("editing");
      setMessage(error instanceof Error ? error.message : "Administrator creation failed.");
    }
  }

  if (state === "created") {
    return (
      <section aria-labelledby="bootstrap-title" className="bootstrap-panel success-panel">
        <p className="eyebrow">Installation secured</p>
        <h1 id="bootstrap-title">Welcome, {credentials.username}.</h1>
        <p className="summary" role="status">{message}</p>
        <p className="security-note">No default account exists. Your session can be revoked at any time.</p>
      </section>
    );
  }

  return (
    <section aria-labelledby="bootstrap-title" className="bootstrap-panel">
      <div className="brand-mark" aria-hidden="true">A</div>
      <p className="eyebrow">Local installation · First run</p>
      <h1 id="bootstrap-title">Create the Administrator</h1>
      <p className="summary">
        Secure this installation with its first and only bootstrap account. Apistra does not ship
        with a default credential and does not contact an external identity service.
      </p>
      <form onSubmit={submit} noValidate>
        <label htmlFor="username">Administrator username</label>
        <input
          autoComplete="username"
          id="username"
          maxLength={128}
          onChange={(event) => setCredentials({ ...credentials, username: event.target.value })}
          required
          value={credentials.username}
        />
        <label htmlFor="password">Password</label>
        <input
          autoComplete="new-password"
          id="password"
          maxLength={1024}
          minLength={12}
          onChange={(event) => setCredentials({ ...credentials, password: event.target.value })}
          required
          type="password"
          value={credentials.password}
        />
        <p className="field-help">At least 12 characters. Credentials remain inside this installation.</p>
        {message ? <p className="form-message" role="alert">{message}</p> : null}
        <button disabled={state === "submitting"} type="submit">
          {state === "submitting" ? "Creating Administrator…" : "Create Administrator"}
        </button>
      </form>
      <p className="security-note">Bootstrap closes permanently after the first successful account.</p>
    </section>
  );
}

export { bootstrapAdministrator, validateCredentials } from "./internal/identity-client";
