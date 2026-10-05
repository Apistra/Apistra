"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { csrfToken, currentSession, type SessionView } from "../administration/public";
import {
  createLimitPolicy,
  evaluateLimitPolicy,
  listLimitPolicies,
  listLimitPolicyVersions,
  publishLimitPolicy,
  type LimitDecision,
  type LimitObservation,
  type LimitPolicyInput,
  type LimitPolicyView
} from "./internal/limit-client";

const INITIAL: LimitPolicyInput = {
  name: "interactive-default",
  maximum_duration_seconds: 300,
  maximum_calls: 10,
  maximum_tokens: 20000,
  maximum_cost_minor_units: 150,
  currency: "EUR",
  maximum_concurrency: 2,
  rate_limit_requests: 30,
  rate_limit_window_seconds: 60,
  warning_threshold_percent: null
};

function toInput(policy: LimitPolicyView): LimitPolicyInput {
  return {
    name: policy.name,
    maximum_duration_seconds: policy.maximum_duration_seconds,
    maximum_calls: policy.maximum_calls,
    maximum_tokens: policy.maximum_tokens,
    maximum_cost_minor_units: policy.maximum_cost_minor_units,
    currency: policy.currency,
    maximum_concurrency: policy.maximum_concurrency,
    rate_limit_requests: policy.rate_limit_requests,
    rate_limit_window_seconds: policy.rate_limit_window_seconds,
    warning_threshold_percent: policy.warning_threshold_percent
  };
}

export function LimitsApp({ projectId }: { projectId: string }) {
  const [session, setSession] = useState<SessionView | null>(null);
  const [policies, setPolicies] = useState<LimitPolicyView[]>([]);
  const [selected, setSelected] = useState<LimitPolicyView | null>(null);
  const [form, setForm] = useState<LimitPolicyInput>(INITIAL);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void currentSession().then(async (active) => {
      if (!active) { window.location.assign("/"); return; }
      setSession(active);
      try { setPolicies(await listLimitPolicies(projectId)); }
      catch (caught) { setError(caught instanceof Error ? caught.message : "Policies are unavailable."); }
    });
  }, [projectId]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null); setMessage(null);
    try {
      const created = await createLimitPolicy(
        projectId, form, csrfToken(sessionStorage), crypto.randomUUID(), fetch,
        selected ?? undefined
      );
      setPolicies(await listLimitPolicies(projectId));
      setSelected(created); setEditing(false); setMessage(`Policy version ${created.version} saved.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Policy save failed.");
    }
  }

  async function reloadLatest() {
    if (!selected) return;
    try {
      const latest = (await listLimitPolicyVersions(projectId, selected.policy_id))[0];
      if (latest) { setSelected(latest); setMessage(`Latest revision ${latest.version} loaded. Your input is retained for comparison.`); }
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Reload failed."); }
  }

  if (!session) return <section className="bootstrap-panel" aria-live="polite">Loading limits and policies…</section>;
  return <section className="workspace" aria-labelledby="limits-title">
    <header className="workspace-header"><div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div></header>
    <nav aria-label="Project navigation">
      <a href={`/projects/${projectId}`}>Overview</a><a href={`/projects/${projectId}/secrets`}>Secrets</a>
      <a href={`/projects/${projectId}/endpoints`}>Model Endpoints</a><a href={`/projects/${projectId}/agents`}>Agents</a>
      <a href={`/projects/${projectId}/tools`}>Tools</a><a aria-current="page" href={`/projects/${projectId}/policies/limits`}>Limits &amp; Policies</a><a href="/audit">Audit</a>
    </nav>
    <div className="workspace-content">
      <p className="eyebrow">Project governance</p><h1 id="limits-title">Limits and policies</h1>
      <p className="summary">Each decision uses an exact, immutable policy version and records its boundaries.</p>
      {error ? <p className="form-message" role="alert">{error}</p> : null}
      {message ? <p role="status">{message}</p> : null}
      <button type="button" onClick={() => { setSelected(null); setForm(INITIAL); setEditing(true); }}>Create policy version</button>
      {!policies.length ? <p>No limit policies configured.</p> : null}
      <div className="project-grid">{policies.map((policy) => <article className="project-card" key={policy.policy_id}>
        <h2>{policy.name}</h2><p>Version {policy.version} · {policy.status}</p>
        <button type="button" onClick={() => { setSelected(policy); setForm(toInput(policy)); setEditing(false); }}>Open policy version</button>
        <button type="button" className="secondary" onClick={() => { setSelected(policy); setForm(toInput(policy)); setEditing(true); }}>Create new draft</button>
      </article>)}</div>
      {selected && !editing ? <PolicyDetail key={`${selected.policy_id}@${selected.version}`} projectId={projectId} policy={selected} onPublish={async () => {
        try {
          const published = await publishLimitPolicy(projectId, selected.policy_id, selected.version, csrfToken(sessionStorage));
          setSelected(published); setPolicies(await listLimitPolicies(projectId));
          setMessage(`Policy version ${published.version} published.`);
        } catch (caught) { setError(caught instanceof Error ? caught.message : "Publication failed."); }
      }} /> : null}
      {editing ? <PolicyForm key={selected ? `${selected.policy_id}@${selected.version}` : "new"} form={form} setForm={setForm} onSubmit={save} selected={selected} onReload={reloadLatest} /> : null}
    </div>
  </section>;
}

function PolicyForm({ form, setForm, onSubmit, selected, onReload }: {
  form: LimitPolicyInput;
  setForm: (value: LimitPolicyInput) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  selected: LimitPolicyView | null;
  onReload: () => Promise<void>;
}) {
  const [costText, setCostText] = useState((form.maximum_cost_minor_units / 100).toFixed(2));
  function numberField(key: keyof LimitPolicyInput, label: string, unit: string) {
    return <label key={key}>{label} ({unit})<input type="number" min="1" required value={form[key] ?? ""} onChange={(event) => setForm({ ...form, [key]: Number(event.target.value) })} /></label>;
  }
  return <form onSubmit={(event) => void onSubmit(event)} noValidate>
    <h2>{selected ? `Create draft from revision ${selected.version}` : "Create policy version"}</h2>
    <label>Name<input required maxLength={128} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
    {numberField("maximum_duration_seconds", "Maximum duration", "seconds")}
    {numberField("maximum_calls", "Maximum calls", "calls")}
    {numberField("maximum_tokens", "Maximum tokens", "tokens")}
    <label>Maximum cost ({form.currency})<input required min="0.01" step="0.01" type="number" value={costText} onChange={(event) => { setCostText(event.target.value); setForm({ ...form, maximum_cost_minor_units: Math.round(Number(event.target.value) * 100) }); }} /></label>
    {numberField("maximum_concurrency", "Maximum concurrency", "runs")}
    {numberField("rate_limit_requests", "Rate limit", "requests")}
    {numberField("rate_limit_window_seconds", "Rate window", "seconds")}
    <label>Currency<input required maxLength={3} value={form.currency} onChange={(event) => setForm({ ...form, currency: event.target.value.toUpperCase() })} /></label>
    <label>Warning threshold (%)<input min="1" max="99" type="number" value={form.warning_threshold_percent ?? ""} onChange={(event) => setForm({ ...form, warning_threshold_percent: event.target.value ? Number(event.target.value) : null })} /></label>
    <button type="submit">{selected ? "Save policy draft" : "Create policy version"}</button>
    {selected ? <button className="secondary" onClick={() => void onReload()} type="button">Reload latest version</button> : null}
  </form>;
}

function PolicyDetail({ projectId, policy, onPublish }: {
  projectId: string; policy: LimitPolicyView; onPublish: () => Promise<void>;
}) {
  const [decision, setDecision] = useState<LimitDecision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [costText, setCostText] = useState("0.00");
  const [observation, setObservation] = useState<LimitObservation>({
    duration_seconds: 0, calls: 0, tokens: 0, cost_minor_units: 0,
    concurrency: 0, requests_in_window: 0, rate_window_seconds: policy.rate_limit_window_seconds
  });
  async function evaluate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null);
    try { setDecision(await evaluateLimitPolicy(projectId, policy.policy_id, policy.version, observation, csrfToken(sessionStorage))); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Decision unavailable."); }
  }
  return <section aria-label="Policy version">
    <h2>{policy.name}@{policy.version}</h2><p>{policy.status} · Published versions are read-only.</p>
    {policy.status === "DRAFT" ? <button type="button" onClick={() => void onPublish()}>Publish policy version</button> : null}
    <dl><dt>Maximum duration</dt><dd>{policy.maximum_duration_seconds} seconds</dd>
      <dt>Maximum calls</dt><dd>{policy.maximum_calls} calls</dd>
      <dt>Maximum tokens</dt><dd>{policy.maximum_tokens} tokens</dd>
      <dt>Maximum cost</dt><dd>{(policy.maximum_cost_minor_units / 100).toFixed(2)} {policy.currency}</dd>
      <dt>Maximum concurrency</dt><dd>{policy.maximum_concurrency} runs</dd>
      <dt>Rate limit</dt><dd>{policy.rate_limit_requests} requests/{policy.rate_limit_window_seconds} seconds</dd></dl>
    {policy.status === "PUBLISHED" ? <form onSubmit={(event) => void evaluate(event)}>
      <h3>Local limit probe</h3>
      {([ ["duration_seconds", "Observed duration (seconds)"], ["calls", "Observed calls"], ["tokens", "Observed tokens"], ["concurrency", "Observed concurrency"], ["requests_in_window", "Observed requests in window"] ] as const).map(([key, label]) =>
        <label key={key}>{label}<input type="number" min="0" value={observation[key]} onChange={(event) => setObservation({ ...observation, [key]: Number(event.target.value) })} /></label>
      )}
      <label>Observed cost ({policy.currency})<input type="number" min="0" step="0.01" value={costText} onChange={(event) => { setCostText(event.target.value); setObservation({ ...observation, cost_minor_units: Math.round(Number(event.target.value) * 100) }); }} /></label>
      <button type="submit">Evaluate limits</button>
    </form> : <p>Publish this draft before evaluating a run.</p>}
    {error ? <p role="alert">{error}</p> : null}
    {decision ? <p role="status">{decision.decision} · {decision.action} · policy version {decision.policy_version} · {decision.violated_limits.join(", ") || "no hard limit exceeded"}</p> : null}
  </section>;
}
