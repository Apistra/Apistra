"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { csrfToken, currentSession, type SessionView } from "../administration/public";
import {
  createTool,
  listTools,
  type EffectClass,
  type ToolVersionInput,
  type ToolVersionView
} from "./internal/tool-client";

const JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema";
const EMPTY_OBJECT_SCHEMA = JSON.stringify({ $schema: JSON_SCHEMA_DIALECT, type: "object" }, null, 2);

export function ToolsApp({ projectId }: { projectId: string }) {
  const [session, setSession] = useState<SessionView | null>(null);
  const [tools, setTools] = useState<ToolVersionView[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void currentSession().then(async (active) => {
      if (!active) { window.location.assign("/"); return; }
      setSession(active);
      try { setTools(await listTools(projectId)); }
      catch (caught) { setError(caught instanceof Error ? caught.message : "Tools are unavailable."); }
    });
  }, [projectId]);

  if (!session) return <section className="bootstrap-panel" aria-live="polite">Loading tools…</section>;
  return <section className="workspace" aria-labelledby="tools-title">
    <header className="workspace-header"><div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div></header>
    <nav aria-label="Project navigation">
      <a href={`/projects/${projectId}`}>Overview</a><a href={`/projects/${projectId}/secrets`}>Secrets</a>
      <a href={`/projects/${projectId}/endpoints`}>Model Endpoints</a><a href={`/projects/${projectId}/agents`}>Agents</a>
      <a aria-current="page" href={`/projects/${projectId}/tools`}>Tools</a><a href={`/projects/${projectId}/policies/limits`}>Limits &amp; Policies</a><a href="/audit">Audit</a>
    </nav>
    <div className="workspace-content">
      <p className="eyebrow">Governed contracts</p><h1 id="tools-title">Tools</h1>
      <p className="summary">Every immutable version declares JSON input/output contracts and one explicit effect class.</p>
      {error ? <p className="form-message" role="alert">{error}</p> : null}
      <button onClick={() => setShowCreate(true)} type="button">Add tool</button>
      {showCreate ? <ToolForm onCancel={() => setShowCreate(false)} onSubmit={async (input) => {
        const created = await createTool(projectId, input, csrfToken(sessionStorage), crypto.randomUUID());
        setTools((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)));
        setShowCreate(false);
      }} /> : null}
      {!tools.length ? <p>No tools configured.</p> : null}
      <div className="project-grid">{tools.map((tool) => <ToolCard key={`${tool.tool_id}@${tool.version}`} tool={tool} />)}</div>
    </div>
  </section>;
}

function ToolCard({ tool }: { tool: ToolVersionView }) {
  const protectedEffect = tool.effect_class !== "READ";
  return <article className="project-card">
    <span>{tool.status}</span><h2>{tool.name}</h2><p>Version {tool.version}</p>
    <p>Effect class: <strong>{effectLabel(tool.effect_class)}</strong></p>
    {protectedEffect ? <p role="status">Approval required by default</p> : null}
    <p>Actions: {tool.actions.join(", ")}</p>
    <details><summary>Versioned contract</summary><pre>{JSON.stringify({ input: tool.input_schema, output: tool.output_schema }, null, 2)}</pre></details>
  </article>;
}

function effectLabel(effect: EffectClass) {
  return effect === "ADMINISTRATIVE" ? "Administrative" : effect === "WRITE" ? "Write" : "Read";
}

function ToolForm({ onCancel, onSubmit }: {
  onCancel: () => void;
  onSubmit: (input: ToolVersionInput) => Promise<void>;
}) {
  const [name, setName] = useState(""); const [description, setDescription] = useState("");
  const [effect, setEffect] = useState<EffectClass>("READ"); const [actions, setActions] = useState("");
  const [inputSchema, setInputSchema] = useState(EMPTY_OBJECT_SCHEMA);
  const [outputSchema, setOutputSchema] = useState(EMPTY_OBJECT_SCHEMA);
  const [error, setError] = useState<string | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null);
    try {
      await onSubmit({
        name, description, effect_class: effect,
        actions: actions.split(",").map((item) => item.trim()).filter(Boolean),
        input_schema: JSON.parse(inputSchema) as Record<string, unknown>,
        output_schema: JSON.parse(outputSchema) as Record<string, unknown>
      });
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Tool creation failed."); }
  }
  return <form onSubmit={submit} noValidate>
    <label htmlFor="tool-name">Name</label><input id="tool-name" maxLength={128} value={name} onChange={(event) => setName(event.target.value)} />
    <label htmlFor="tool-description">Description</label><textarea id="tool-description" maxLength={4096} value={description} onChange={(event) => setDescription(event.target.value)} />
    <label htmlFor="tool-effect">Effect class</label><select id="tool-effect" value={effect} onChange={(event) => setEffect(event.target.value as EffectClass)}><option value="READ">Read</option><option value="WRITE">Write</option><option value="ADMINISTRATIVE">Administrative</option></select>
    {effect !== "READ" ? <p role="status">Approval required by default</p> : null}
    <label htmlFor="tool-actions">Actions</label><input id="tool-actions" placeholder="search, replace" value={actions} onChange={(event) => setActions(event.target.value)} />
    <label htmlFor="tool-input-schema">Input schema</label><textarea id="tool-input-schema" value={inputSchema} onChange={(event) => setInputSchema(event.target.value)} />
    <label htmlFor="tool-output-schema">Output schema</label><textarea id="tool-output-schema" value={outputSchema} onChange={(event) => setOutputSchema(event.target.value)} />
    {error ? <p className="form-message" role="alert">{error}</p> : null}
    <button disabled={!name || !actions} type="submit">Add tool</button><button className="secondary" onClick={onCancel} type="button">Cancel</button>
  </form>;
}
