"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  csrfToken,
  currentSession,
  type SessionView
} from "../administration/public";
import {
  listSecrets,
  replaceSecret,
  storeSecret,
  type SecretReferenceView
} from "./internal/secret-client";

export function SecretReferencesApp({ projectId }: { projectId: string }) {
  const [session, setSession] = useState<SessionView | null>(null);
  const [references, setReferences] = useState<SecretReferenceView[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [replaceId, setReplaceId] = useState<string | null>(null);
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
        setReferences(await listSecrets(projectId));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Secret reference is unavailable.");
      }
    });
  }, [projectId]);

  function updateReference(updated: SecretReferenceView) {
    setReferences((current) => [
      ...current.filter((item) => item.id !== updated.id),
      updated
    ].sort((left, right) => left.name.localeCompare(right.name)));
  }

  if (!session) {
    return <section className="bootstrap-panel" aria-live="polite">Loading secret references…</section>;
  }
  return (
    <section className="workspace" aria-labelledby="secret-references-title">
      <header className="workspace-header">
        <div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div>
      </header>
      <nav aria-label="Project navigation">
        <a href={`/projects/${projectId}`}>Overview</a>
        <a aria-current="page" href={`/projects/${projectId}/secrets`}>Secrets</a>
        <a href={`/projects/${projectId}/endpoints`}>Endpoints</a>
        <a href="/audit">Audit</a>
      </nav>
      <div className="workspace-content">
        <p className="eyebrow">Write-only project credentials</p>
        <h1 id="secret-references-title">Secret references</h1>
        <p className="summary">Values are encrypted and cannot be viewed again after storage.</p>
        {message ? <p className="form-message" role="status">{message}</p> : null}
        {error ? <p className="form-message" role="alert">{error}</p> : null}
        <button onClick={() => { setShowCreate(true); setMessage(null); }} type="button">Add secret</button>
        {showCreate ? <SecretForm
          onCancel={() => setShowCreate(false)}
          onSubmit={async (name, purpose, value) => {
            const stored = await storeSecret(
              projectId,
              { name, purpose, value },
              csrfToken(sessionStorage),
              crypto.randomUUID()
            );
            updateReference(stored);
            setShowCreate(false);
            setMessage("Secret stored. The value cannot be viewed again.");
          }}
        /> : null}
        <div className="project-grid">
          {references.map((reference) => <article className="project-card" key={reference.id}>
            <span>{reference.status}</span>
            <h2>{reference.name}</h2>
            <p>{reference.purpose}</p>
            <code>{reference.id}</code>
            <p>Version {reference.version} · Envelope {reference.envelope_version}</p>
            <p>Updated {new Date(reference.updated_at).toISOString()}</p>
            {reference.status === "ACTIVE" ? <button className="secondary" onClick={() => setReplaceId(reference.id)} type="button">Replace value</button> : null}
            {replaceId === reference.id ? <ReplacementForm
              onCancel={() => setReplaceId(null)}
              onSubmit={async (value) => {
                updateReference(await replaceSecret(
                  reference,
                  value,
                  csrfToken(sessionStorage)
                ));
                setReplaceId(null);
                setMessage("Secret stored. The value cannot be viewed again.");
              }}
            /> : null}
          </article>)}
        </div>
      </div>
    </section>
  );
}

function SecretForm({ onCancel, onSubmit }: {
  onCancel: () => void;
  onSubmit: (name: string, purpose: string, value: string) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await onSubmit(name, purpose, value);
    } catch (caught) {
      setValue("");
      setError(caught instanceof Error ? caught.message : "Secret storage failed.");
    }
  }
  return (
    <form onSubmit={submit} noValidate>
      <label htmlFor="secret-name">Name</label>
      <input id="secret-name" maxLength={64} value={name} onChange={(event) => setName(event.target.value)} />
      <label htmlFor="secret-purpose">Purpose</label>
      <input id="secret-purpose" maxLength={256} value={purpose} onChange={(event) => setPurpose(event.target.value)} />
      <label htmlFor="secret-value">Secret value</label>
      <input id="secret-value" autoComplete="new-password" type="password" value={value} onChange={(event) => setValue(event.target.value)} />
      {error ? <p className="form-message" role="alert">{error}</p> : null}
      <button disabled={!name || !purpose || !value} type="submit">Store secret</button>
      <button className="secondary" onClick={onCancel} type="button">Cancel</button>
    </form>
  );
}

function ReplacementForm({ onCancel, onSubmit }: {
  onCancel: () => void;
  onSubmit: (value: string) => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await onSubmit(value);
    } catch (caught) {
      setValue("");
      setError(caught instanceof Error ? caught.message : "Secret replacement failed.");
    }
  }
  return (
    <form onSubmit={submit} noValidate>
      <label htmlFor="replacement-value">Secret value</label>
      <input id="replacement-value" autoComplete="new-password" type="password" value={value} onChange={(event) => setValue(event.target.value)} />
      {error ? <p className="form-message" role="alert">{error}</p> : null}
      <button disabled={!value} type="submit">Store secret</button>
      <button className="secondary" onClick={onCancel} type="button">Cancel</button>
    </form>
  );
}
