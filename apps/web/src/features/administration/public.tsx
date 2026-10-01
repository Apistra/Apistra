"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  bootstrapAdministrator,
  currentSession,
  installationStatus,
  signIn,
  signOut,
  type Credentials,
  type SessionView,
  validateCredentials
} from "./internal/identity-client";
import { createProject, listProjects, type ProjectView } from "./internal/project-client";

type Screen = "loading" | "sign-in" | "bootstrap" | "overview" | "create-project";
const CSRF_STORAGE_KEY = "apistra.csrf";

export function AdministrationApp() {
  const [screen, setScreen] = useState<Screen>("loading");
  const [bootstrapAvailable, setBootstrapAvailable] = useState(false);
  const [session, setSession] = useState<SessionView | null>(null);
  const [projects, setProjects] = useState<ProjectView[]>([]);
  const [currentProject, setCurrentProject] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function openOverview(activeSession: SessionView) {
    const availableProjects = await listProjects();
    setSession(activeSession);
    setProjects(availableProjects);
    setCurrentProject(availableProjects.find((item) => item.status === "ACTIVE")?.id ?? "");
    setScreen("overview");
  }

  useEffect(() => {
    void Promise.all([installationStatus(), currentSession()])
      .then(async ([installation, activeSession]) => {
        setBootstrapAvailable(installation.bootstrap_available);
        if (activeSession) await openOverview(activeSession);
        else setScreen("sign-in");
      })
      .catch(() => {
        setMessage("The local service is unavailable.");
        setScreen("sign-in");
      });
  }, []);

  function acceptSession(receipt: SessionView & { csrf_token: string }) {
    sessionStorage.setItem(CSRF_STORAGE_KEY, receipt.csrf_token);
    return openOverview(receipt);
  }

  async function doSignOut() {
    const csrf = sessionStorage.getItem(CSRF_STORAGE_KEY) ?? "";
    try {
      await signOut(csrf);
    } finally {
      sessionStorage.removeItem(CSRF_STORAGE_KEY);
      setSession(null);
      setProjects([]);
      setScreen("sign-in");
    }
  }

  if (screen === "loading") {
    return <section className="bootstrap-panel" aria-live="polite">Loading local installation…</section>;
  }
  if (screen === "bootstrap") {
    return <AdministratorBootstrap onCancel={() => setScreen("sign-in")} onCreated={acceptSession} />;
  }
  if (screen === "sign-in") {
    return (
      <SignIn
        bootstrapAvailable={bootstrapAvailable}
        message={message}
        onBootstrap={() => setScreen("bootstrap")}
        onSignedIn={acceptSession}
      />
    );
  }
  if (screen === "create-project") {
    return (
      <ProjectCreate
        onCancel={() => setScreen("overview")}
        onCreated={(project) => {
          setProjects([...projects, project]);
          setCurrentProject(project.id);
          setScreen("overview");
        }}
      />
    );
  }
  return (
    <ProjectOverview
      currentProject={currentProject}
      onCreate={() => setScreen("create-project")}
      onProjectChange={setCurrentProject}
      onSignOut={doSignOut}
      projects={projects}
      session={session!}
    />
  );
}

function SignIn({ bootstrapAvailable, message, onBootstrap, onSignedIn }: {
  bootstrapAvailable: boolean;
  message: string | null;
  onBootstrap: () => void;
  onSignedIn: (receipt: SessionView & { csrf_token: string }) => void;
}) {
  const [credentials, setCredentials] = useState<Credentials>({ username: "", password: "" });
  const [error, setError] = useState<string | null>(message);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSignedIn(await signIn(credentials));
    } catch {
      setCredentials({ ...credentials, password: "" });
      setError("Sign-in failed. Check your credentials and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section aria-labelledby="sign-in-title" className="bootstrap-panel">
      <div className="brand-mark" aria-hidden="true">A</div>
      <p className="eyebrow">Local installation</p>
      <h1 id="sign-in-title">Sign in</h1>
      <p className="summary">Administer isolated AI business-process projects without an external identity service.</p>
      <form onSubmit={submit} noValidate>
        <label htmlFor="username">Username</label>
        <input id="username" autoComplete="username" value={credentials.username} onChange={(event) => setCredentials({ ...credentials, username: event.target.value })} />
        <label htmlFor="password">Password</label>
        <input id="password" autoComplete="current-password" type="password" value={credentials.password} onChange={(event) => setCredentials({ ...credentials, password: event.target.value })} />
        {error ? <p className="form-message" role="alert">{error}</p> : null}
        <button disabled={submitting} type="submit">{submitting ? "Signing in…" : "Sign in"}</button>
        {bootstrapAvailable ? <button className="secondary" onClick={onBootstrap} type="button">Create Administrator</button> : null}
      </form>
    </section>
  );
}

export function AdministratorBootstrap({ onCancel = () => undefined, onCreated }: {
  onCancel?: () => void;
  onCreated?: (receipt: SessionView & { csrf_token: string }) => void;
}) {
  const [credentials, setCredentials] = useState<Credentials>({ username: "", password: "" });
  const [confirmation, setConfirmation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validation = validateCredentials(credentials);
    if (validation || credentials.password !== confirmation) {
      setMessage(validation ?? "Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      const receipt = await bootstrapAdministrator(credentials);
      onCreated?.(receipt);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Administrator creation failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section aria-labelledby="bootstrap-title" className="bootstrap-panel">
      <p className="eyebrow">Local installation · First run</p>
      <h1 id="bootstrap-title">Create Administrator</h1>
      <p className="summary">No default account exists. Bootstrap closes after the first successful account.</p>
      <form onSubmit={submit} noValidate>
        <label htmlFor="bootstrap-username">Username</label>
        <input id="bootstrap-username" autoComplete="username" maxLength={128} value={credentials.username} onChange={(event) => setCredentials({ ...credentials, username: event.target.value })} />
        <label htmlFor="bootstrap-password">Password</label>
        <input id="bootstrap-password" autoComplete="new-password" maxLength={1024} minLength={12} type="password" value={credentials.password} onChange={(event) => setCredentials({ ...credentials, password: event.target.value })} />
        <label htmlFor="confirm-password">Confirm password</label>
        <input id="confirm-password" autoComplete="new-password" type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
        {message ? <p className="form-message" role="alert">{message}</p> : null}
        <button disabled={submitting} type="submit">{submitting ? "Creating Administrator…" : "Create Administrator"}</button>
        <button className="secondary" onClick={onCancel} type="button">Back to sign in</button>
      </form>
    </section>
  );
}

function ProjectOverview({ currentProject, onCreate, onProjectChange, onSignOut, projects, session }: {
  currentProject: string;
  onCreate: () => void;
  onProjectChange: (id: string) => void;
  onSignOut: () => void;
  projects: ProjectView[];
  session: SessionView;
}) {
  return (
    <section className="workspace" aria-labelledby="project-overview-title">
      <header className="workspace-header">
        <div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div>
        <label>Current project<select aria-label="Current project" value={currentProject} onChange={(event) => onProjectChange(event.target.value)}><option value="">No project selected</option>{projects.filter((item) => item.status === "ACTIVE").map((project) => <option key={project.id} value={project.id}>{project.key} · {project.name}</option>)}</select></label>
        <button aria-label="Administrator menu" className="secondary compact" onClick={onSignOut} type="button">Sign out</button>
      </header>
      <nav aria-label="Project navigation"><a aria-current="page" href="#overview">Overview</a><span aria-disabled="true">Audit</span></nav>
      <div className="workspace-content">
        <p className="eyebrow">Installation secured</p>
        <h1 id="project-overview-title">Project overview</h1>
        {projects.length === 0 ? <p className="summary">No project exists yet. Create the first isolated project.</p> : <div className="project-grid">{projects.map((project) => <article className="project-card" key={project.id}><span>{project.status}</span><h2>{project.name}</h2><p>{project.key} · Version {project.version}</p></article>)}</div>}
        <button onClick={onCreate} type="button">Create project</button>
      </div>
    </section>
  );
}

function ProjectCreate({ onCancel, onCreated }: { onCancel: () => void; onCreated: (project: ProjectView) => void }) {
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const ready = name.trim().length > 0 && key.trim().length > 0;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ready) { setError("This field is required."); return; }
    try {
      const csrf = sessionStorage.getItem(CSRF_STORAGE_KEY) ?? "";
      onCreated(await createProject({ name, key: key.toUpperCase() }, csrf, crypto.randomUUID()));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Project creation failed.");
    }
  }

  return (
    <section className="bootstrap-panel" aria-labelledby="project-create-title">
      <p className="eyebrow">Isolated workspace</p><h1 id="project-create-title">Create project</h1>
      <form onSubmit={submit} noValidate>
        <label htmlFor="project-name">Project name</label><input id="project-name" maxLength={128} value={name} onChange={(event) => setName(event.target.value)} />
        <label htmlFor="project-key">Project key</label><input id="project-key" maxLength={32} pattern="[A-Z0-9-]+" value={key} onChange={(event) => setKey(event.target.value.toUpperCase())} />
        {error ? <p className="form-message" role="alert">{error}</p> : null}
        <button disabled={!ready} type="submit">Create project</button><button className="secondary" onClick={onCancel} type="button">Cancel</button>
      </form>
    </section>
  );
}

export { bootstrapAdministrator, validateCredentials } from "./internal/identity-client";
