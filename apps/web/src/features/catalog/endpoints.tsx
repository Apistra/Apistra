"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { csrfToken, currentSession, type SessionView } from "../administration/public";
import {
  listEndpoints,
  storeEndpoint,
  testEndpoint,
  type EndpointInput,
  type EndpointPurpose,
  type EndpointView,
  type NetworkProfile
} from "./internal/endpoint-client";
import { listSecrets, type SecretReferenceView } from "./internal/secret-client";

const OUTCOME_LABELS = {
  CONNECTION_VERIFIED: "Connection verified",
  CONNECTION_FAILED: "Connection failed",
  DESTINATION_BLOCKED: "Destination blocked",
  AUTHENTICATION_FAILED: "Authentication failed",
  TIMED_OUT: "Timed out",
  PROBE_NOT_SUPPORTED: "Probe not supported"
} as const;

export function EndpointCatalogueApp({ projectId }: { projectId: string }) {
  const [session, setSession] = useState<SessionView | null>(null);
  const [endpoints, setEndpoints] = useState<EndpointView[]>([]);
  const [secrets, setSecrets] = useState<SecretReferenceView[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void currentSession().then(async (activeSession) => {
      if (!activeSession) {
        window.location.assign("/");
        return;
      }
      setSession(activeSession);
      try {
        const [loadedEndpoints, loadedSecrets] = await Promise.all([
          listEndpoints(projectId),
          listSecrets(projectId)
        ]);
        setEndpoints(loadedEndpoints);
        setSecrets(loadedSecrets.filter((item) => item.status === "ACTIVE"));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Endpoint catalogue is unavailable.");
      }
    });
  }, [projectId]);

  function updateEndpoint(updated: EndpointView) {
    setEndpoints((current) => [
      ...current.filter((item) => item.id !== updated.id),
      updated
    ].sort((left, right) => left.name.localeCompare(right.name)));
  }

  if (!session) {
    return <section className="bootstrap-panel" aria-live="polite">Loading model endpoints…</section>;
  }
  return (
    <section className="workspace" aria-labelledby="model-endpoints-title">
      <header className="workspace-header">
        <div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div>
      </header>
      <nav aria-label="Project navigation">
        <a href={`/projects/${projectId}`}>Overview</a>
        <a href={`/projects/${projectId}/secrets`}>Secrets</a>
        <a aria-current="page" href={`/projects/${projectId}/endpoints`}>Endpoints</a>
        <a href="/audit">Audit</a>
      </nav>
      <div className="workspace-content">
        <p className="eyebrow">Provider-neutral configuration</p>
        <h1 id="model-endpoints-title">Model endpoints</h1>
        <p className="summary">Saving is offline. Test connection performs one bounded, read-only probe.</p>
        {message ? <p className="form-message" role="status">{message}</p> : null}
        {error ? <p className="form-message" role="alert">{error}</p> : null}
        <button onClick={() => { setShowCreate(true); setMessage(null); }} type="button">Add endpoint</button>
        {showCreate ? <EndpointForm
          secrets={secrets}
          onCancel={() => setShowCreate(false)}
          onSubmit={async (input) => {
            updateEndpoint(await storeEndpoint(
              projectId,
              input,
              csrfToken(sessionStorage),
              crypto.randomUUID()
            ));
            setShowCreate(false);
            setMessage("Endpoint saved without contacting the provider.");
          }}
        /> : null}
        {!endpoints.length ? <p>No model endpoints configured.</p> : null}
        <div className="project-grid">
          {endpoints.map((endpoint) => <article className="project-card" key={endpoint.id}>
            <span>{endpoint.status}</span>
            <h2>{endpoint.name}</h2>
            <p>{endpoint.purpose} · {endpoint.provider_protocol}</p>
            <code>{endpoint.base_url}</code>
            <p>Model: {endpoint.model_identifier}</p>
            <p>Network: {endpoint.network_profile} · Version {endpoint.version}</p>
            {endpoint.last_probe_outcome ? <p>{OUTCOME_LABELS[endpoint.last_probe_outcome]}</p> : null}
            <button
              className="secondary"
              disabled={testingId !== null}
              onClick={async () => {
                setTestingId(endpoint.id);
                setError(null);
                try {
                  const updated = await testEndpoint(endpoint, csrfToken(sessionStorage));
                  updateEndpoint(updated);
                  setMessage(updated.last_probe_outcome
                    ? OUTCOME_LABELS[updated.last_probe_outcome]
                    : "Connection test completed.");
                } catch (caught) {
                  setError(caught instanceof Error ? caught.message : "Connection test failed.");
                } finally {
                  setTestingId(null);
                }
              }}
              type="button"
            >{testingId === endpoint.id ? "Testing…" : "Test connection"}</button>
          </article>)}
        </div>
      </div>
    </section>
  );
}

function EndpointForm({ secrets, onCancel, onSubmit }: {
  secrets: SecretReferenceView[];
  onCancel: () => void;
  onSubmit: (input: EndpointInput) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState<EndpointPurpose>("GENERATIVE");
  const [baseUrl, setBaseUrl] = useState("");
  const [modelIdentifier, setModelIdentifier] = useState("");
  const [secretReferenceId, setSecretReferenceId] = useState("");
  const [networkProfile, setNetworkProfile] = useState<NetworkProfile>("CLOUD");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await onSubmit({
        name,
        purpose,
        provider_protocol: "OPENAI_COMPATIBLE",
        base_url: baseUrl,
        model_identifier: modelIdentifier,
        secret_reference_id: secretReferenceId,
        network_profile: networkProfile
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Endpoint storage failed.");
    }
  }
  const valid = name && baseUrl && modelIdentifier && secretReferenceId;
  return (
    <form onSubmit={submit} noValidate>
      <label htmlFor="endpoint-name">Name</label>
      <input id="endpoint-name" maxLength={64} value={name} onChange={(event) => setName(event.target.value)} />
      <label htmlFor="endpoint-purpose">Purpose</label>
      <select id="endpoint-purpose" value={purpose} onChange={(event) => setPurpose(event.target.value as EndpointPurpose)}>
        <option value="GENERATIVE">Generative</option><option value="EMBEDDING">Embedding</option>
      </select>
      <label htmlFor="endpoint-protocol">Provider protocol</label>
      <input id="endpoint-protocol" readOnly value="OpenAI-compatible" />
      <label htmlFor="endpoint-url">Base URL</label>
      <input id="endpoint-url" type="url" value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
      <label htmlFor="endpoint-model">Model identifier</label>
      <input id="endpoint-model" maxLength={256} value={modelIdentifier} onChange={(event) => setModelIdentifier(event.target.value)} />
      <label htmlFor="endpoint-secret">Secret reference</label>
      <select id="endpoint-secret" value={secretReferenceId} onChange={(event) => setSecretReferenceId(event.target.value)}>
        <option value="">Select a secret</option>
        {secrets.map((secret) => <option key={secret.id} value={secret.id}>{secret.name}</option>)}
      </select>
      <label htmlFor="endpoint-network">Network profile</label>
      <select id="endpoint-network" value={networkProfile} onChange={(event) => setNetworkProfile(event.target.value as NetworkProfile)}>
        <option value="CLOUD">Cloud</option><option value="ON_PREMISE">On-premise</option><option value="LOCAL">Local</option>
      </select>
      {error ? <p className="form-message" role="alert">{error}</p> : null}
      <button disabled={!valid} type="submit">Save endpoint</button>
      <button className="secondary" onClick={onCancel} type="button">Cancel</button>
    </form>
  );
}
