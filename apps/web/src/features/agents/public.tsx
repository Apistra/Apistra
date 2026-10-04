"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { csrfToken, currentSession, type SessionView } from "../administration/public";
import { listEndpoints, type EndpointView } from "../catalog/api";
import {
  createAgent,
  listAgents,
  type AgentVersionInput,
  type AgentVersionView
} from "./internal/agent-client";

export function AgentVersionsApp({ projectId }: { projectId: string }) {
  const [session, setSession] = useState<SessionView | null>(null);
  const [agents, setAgents] = useState<AgentVersionView[]>([]);
  const [endpoints, setEndpoints] = useState<EndpointView[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void currentSession().then(async (active) => {
      if (!active) { window.location.assign("/"); return; }
      setSession(active);
      try {
        const [loadedAgents, loadedEndpoints] = await Promise.all([
          listAgents(projectId), listEndpoints(projectId)
        ]);
        setAgents(loadedAgents);
        setEndpoints(loadedEndpoints.filter((item) => item.purpose === "GENERATIVE"));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Agent versions are unavailable.");
      }
    });
  }, [projectId]);

  if (!session) return <section className="bootstrap-panel" aria-live="polite">Loading agent versions…</section>;
  return <section className="workspace" aria-labelledby="agent-versions-title">
    <header className="workspace-header"><div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div></header>
    <nav aria-label="Project navigation">
      <a href={`/projects/${projectId}`}>Overview</a><a href={`/projects/${projectId}/secrets`}>Secrets</a>
      <a href={`/projects/${projectId}/endpoints`}>Endpoints</a><a aria-current="page" href={`/projects/${projectId}/agents`}>Agents</a><a href="/audit">Audit</a>
    </nav>
    <div className="workspace-content">
      <p className="eyebrow">Immutable configuration</p><h1 id="agent-versions-title">Agent versions</h1>
      <p className="summary">Published versions are read-only. Editing creates a new draft with exact references.</p>
      {error ? <p className="form-message" role="alert">{error}</p> : null}
      <button onClick={() => setShowCreate(true)} type="button">Create agent version</button>
      {showCreate ? <AgentForm endpoints={endpoints} onCancel={() => setShowCreate(false)} onSubmit={async (input) => {
        const created = await createAgent(projectId, input, csrfToken(sessionStorage), crypto.randomUUID());
        setAgents((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)));
        setShowCreate(false);
      }} /> : null}
      {!agents.length ? <p>No agent versions configured.</p> : null}
      <div className="project-grid">{agents.map((agent) => <article className="project-card" key={`${agent.agent_id}@${agent.version}`}>
        <span>{agent.status}</span><h2>{agent.name}</h2><p>Version {agent.version}</p>
        <p>Primary: <code>{agent.primary_endpoint.id}@{agent.primary_endpoint.version}</code></p>
        <p>Fallback: {agent.fallback_endpoint ? <code>{agent.fallback_endpoint.id}@{agent.fallback_endpoint.version}</code> : "None"}</p>
        <p>Tools: {agent.tool_versions.length ? agent.tool_versions.map((item) => `${item.id}@${item.version}`).join(", ") : "None"}</p>
        <p>Limits policy: {agent.limits_policy_version ? `${agent.limits_policy_version.id}@${agent.limits_policy_version.version}` : "None"}</p>
      </article>)}</div>
    </div>
  </section>;
}

function AgentForm({ endpoints, onCancel, onSubmit }: {
  endpoints: EndpointView[];
  onCancel: () => void;
  onSubmit: (input: AgentVersionInput) => Promise<void>;
}) {
  const [name, setName] = useState(""); const [instructions, setInstructions] = useState("");
  const [primary, setPrimary] = useState(""); const [fallback, setFallback] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const primaryEndpoint = endpoints.find((item) => item.id === primary);
    const fallbackEndpoint = endpoints.find((item) => item.id === fallback);
    if (!primaryEndpoint) return;
    await onSubmit({
      name, instructions,
      primary_endpoint: { id: primaryEndpoint.id, version: primaryEndpoint.version },
      fallback_endpoint: fallbackEndpoint ? { id: fallbackEndpoint.id, version: fallbackEndpoint.version } : null,
      tool_versions: [], limits_policy_version: null
    });
  }
  return <form onSubmit={submit} noValidate>
    <label htmlFor="agent-name">Agent name</label><input id="agent-name" maxLength={128} value={name} onChange={(event) => setName(event.target.value)} />
    <label htmlFor="agent-instructions">Instructions</label><textarea id="agent-instructions" maxLength={32768} value={instructions} onChange={(event) => setInstructions(event.target.value)} />
    <label htmlFor="agent-primary">Primary endpoint</label><select id="agent-primary" value={primary} onChange={(event) => setPrimary(event.target.value)}><option value="">Select an endpoint</option>{endpoints.map((item) => <option key={item.id} value={item.id}>{item.name} @ {item.version}</option>)}</select>
    <label htmlFor="agent-fallback">Fallback endpoint (optional)</label><select id="agent-fallback" value={fallback} onChange={(event) => setFallback(event.target.value)}><option value="">No fallback</option>{endpoints.filter((item) => item.id !== primary).map((item) => <option key={item.id} value={item.id}>{item.name} @ {item.version}</option>)}</select>
    <label>Tool set</label><p>No tool versions available until the tool catalogue is configured.</p>
    <label>Limits policy</label><p>No limits policy selected.</p>
    <button disabled={!name || !instructions || !primary} type="submit">Create agent version</button><button className="secondary" onClick={onCancel} type="button">Cancel</button>
  </form>;
}
