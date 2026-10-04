"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import {
  bootstrapAdministrator,
  csrfToken,
  currentSession,
  installationStatus,
  missingSessionMessage,
  rememberAuthenticatedSession,
  revokeAuthenticatedSession,
  signIn,
  type Credentials,
  type SessionView,
  focusErrorAlert,
  validateCredentials
} from "./internal/identity-client";
import {
  createProject,
  listAuditEvents,
  listProjects,
  type AuditEventView,
  type ProjectView
} from "./internal/project-client";

type Screen = "loading" | "sign-in" | "bootstrap" | "overview" | "create-project" | "audit" | "installation-status" | "not-found";

export function AdministrationApp({ requestedProjectId, initialView = "overview" }: {
  requestedProjectId?: string;
  initialView?: "overview" | "audit" | "bootstrap";
}) {
  const [screen, setScreen] = useState<Screen>("loading");
  const [bootstrapAvailable, setBootstrapAvailable] = useState(false);
  const [session, setSession] = useState<SessionView | null>(null);
  const [projects, setProjects] = useState<ProjectView[]>([]);
  const [currentProject, setCurrentProject] = useState("");
  const [auditEvents, setAuditEvents] = useState<AuditEventView[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  async function openOverview(activeSession: SessionView) {
    const availableProjects = await listProjects();
    setSession(activeSession);
    setProjects(availableProjects);
    if (requestedProjectId && !availableProjects.some((item) => item.id === requestedProjectId)) {
      setScreen("not-found");
      return;
    }
    setCurrentProject(requestedProjectId ?? availableProjects.find((item) => item.status === "ACTIVE")?.id ?? "");
    if (initialView === "audit") {
      setAuditEvents(await listAuditEvents());
      setScreen("audit");
    } else {
      setScreen("overview");
    }
  }

  useEffect(() => {
    void Promise.all([installationStatus(), currentSession()])
      .then(async ([installation, activeSession]) => {
        setBootstrapAvailable(installation.bootstrap_available);
        if (initialView === "bootstrap") {
          setSession(activeSession);
          setScreen(installation.bootstrap_available ? "bootstrap" : "installation-status");
        } else if (activeSession) {
          await openOverview(activeSession);
        } else {
          setMessage(missingSessionMessage(sessionStorage));
          setScreen("sign-in");
        }
      })
      .catch(() => {
        setMessage("The local service is unavailable.");
        setScreen("sign-in");
      });
  }, []);

  function acceptSession(receipt: SessionView & { csrf_token: string }) {
    rememberAuthenticatedSession(sessionStorage, receipt.csrf_token);
    return openOverview(receipt);
  }

  async function doSignOut() {
    await revokeAuthenticatedSession(sessionStorage);
    setSession(null);
    setProjects([]);
    setScreen("sign-in");
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
  if (screen === "installation-status") {
    return (
      <InstallationStatus
        onBack={() => setScreen(session ? "overview" : "sign-in")}
        onSignOut={doSignOut}
        session={session}
      />
    );
  }
  if (screen === "not-found") {
    return <ProjectNotFound onInstallationStatus={() => setScreen("installation-status")} onSignOut={doSignOut} session={session!} />;
  }
  if (screen === "audit") {
    return <AuditLog events={auditEvents} onInstallationStatus={() => setScreen("installation-status")} onSignOut={doSignOut} session={session!} />;
  }
  return (
    <ProjectOverview
      currentProject={currentProject}
      onCreate={() => setScreen("create-project")}
      onInstallationStatus={() => setScreen("installation-status")}
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
  const errorRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (error) focusErrorAlert(errorRef.current);
  }, [error]);

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
        {error ? <p className="form-message" ref={errorRef} role="alert" tabIndex={-1}>{error}</p> : null}
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
      <h1 id="bootstrap-title">Bootstrap Administrator</h1>
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

function ProjectOverview({ currentProject, onCreate, onInstallationStatus, onProjectChange, onSignOut, projects, session }: {
  currentProject: string;
  onCreate: () => void;
  onInstallationStatus: () => void;
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
        <AdministratorMenu onInstallationStatus={onInstallationStatus} onSignOut={onSignOut} />
      </header>
      <nav aria-label="Project navigation"><a aria-current="page" href="/">Overview</a><a href="/audit">Audit</a></nav>
      <div className="workspace-content">
        <p className="eyebrow">Installation secured</p>
        <h1 id="project-overview-title">Project overview</h1>
        {projects.length === 0 ? <p className="summary">No project exists yet. Create the first isolated project.</p> : <div className="project-grid">{projects.map((project) => <article className="project-card" key={project.id}><span>{project.status}</span><h2><a href={`/projects/${project.id}`}>{project.name}</a></h2><p>{project.key} · Version {project.version}</p></article>)}</div>}
        <button onClick={onCreate} type="button">Create project</button>
      </div>
    </section>
  );
}

export function AuditLog({ events, onInstallationStatus, onSignOut, session }: {
  events: AuditEventView[];
  onInstallationStatus: () => void;
  onSignOut: () => void;
  session: SessionView;
}) {
  return (
    <section className="workspace" aria-labelledby="audit-title">
      <header className="workspace-header"><div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div><AdministratorMenu onInstallationStatus={onInstallationStatus} onSignOut={onSignOut} /></header>
      <nav aria-label="Project navigation"><a href="/">Overview</a><a aria-current="page" href="/audit">Audit</a></nav>
      <div className="workspace-content"><p className="eyebrow">Attributable evidence</p><h1 id="audit-title">Audit log</h1>{events.length === 0 ? <p className="summary">No audit events are available.</p> : <ol className="audit-list">{events.map((event) => <li key={event.id}><strong>{event.event_type}</strong><span>{event.actor ?? "System"} · {new Date(event.created_at).toISOString()}</span>{event.installation_id ? <code>Installation: {event.installation_id}</code> : null}{event.project_key ? <code>Project: {event.project_key}</code> : null}<code>Correlation: {event.correlation_id}</code></li>)}</ol>}</div>
    </section>
  );
}

function ProjectNotFound({ onInstallationStatus, onSignOut, session }: { onInstallationStatus: () => void; onSignOut: () => void; session: SessionView }) {
  return (
    <section className="workspace" aria-labelledby="not-found-title">
      <header className="workspace-header"><div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div><AdministratorMenu onInstallationStatus={onInstallationStatus} onSignOut={onSignOut} /></header>
      <nav aria-label="Project navigation"><a href="/">Overview</a><a href="/audit">Audit</a></nav>
      <div className="workspace-content"><p className="eyebrow">Safe project boundary</p><h1 id="not-found-title">Project not found</h1><p className="summary">The project does not exist or you do not have access.</p></div>
    </section>
  );
}

export function ProjectCreate({ onCancel, onCreated }: { onCancel: () => void; onCreated: (project: ProjectView) => void }) {
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const ready = name.trim().length > 0 && key.trim().length > 0;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ready) { setError("This field is required."); return; }
    try {
      const csrf = csrfToken(sessionStorage);
      onCreated(await createProject({ name, key: key.toUpperCase() }, csrf, crypto.randomUUID()));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Project creation failed.");
    }
  }

  return (
    <section className="bootstrap-panel" aria-labelledby="project-create-title">
      <p className="eyebrow">Isolated workspace</p><h1 id="project-create-title">Project creation</h1>
      <form onSubmit={submit} noValidate>
        <label htmlFor="project-name">Project name</label><input id="project-name" maxLength={128} value={name} onChange={(event) => setName(event.target.value)} />
        <label htmlFor="project-key">Project key</label><input id="project-key" maxLength={32} pattern="[A-Z0-9-]+" value={key} onChange={(event) => setKey(event.target.value.toUpperCase())} />
        {error ? <p className="form-message" role="alert">{error}</p> : null}
        <button disabled={!ready} type="submit">Create project</button><button className="secondary" onClick={onCancel} type="button">Cancel</button>
      </form>
    </section>
  );
}

export function AdministratorMenu({ onInstallationStatus, onSignOut }: {
  onInstallationStatus: () => void;
  onSignOut: () => void;
}) {
  return (
    <details className="administrator-menu">
      <summary aria-label="Administrator menu">Administrator menu</summary>
      <div aria-label="Administrator actions" className="administrator-actions">
        <button className="secondary compact" onClick={onInstallationStatus} type="button">Installation status</button>
        <button className="secondary compact" onClick={onSignOut} type="button">Sign out</button>
      </div>
    </details>
  );
}

export function InstallationStatus({ onBack, onSignOut, session }: {
  onBack: () => void;
  onSignOut: () => void;
  session: SessionView | null;
}) {
  const content = (
    <div className="workspace-content">
      <p className="eyebrow">Local installation</p>
      <h1 id="installation-status-title">Installation status</h1>
      <p className="summary">Administrator bootstrap is complete.</p>
      <button className="secondary" onClick={onBack} type="button">{session ? "Back to projects" : "Back to sign in"}</button>
    </div>
  );
  if (!session) return <section aria-labelledby="installation-status-title" className="bootstrap-panel">{content}</section>;
  return (
    <section aria-labelledby="installation-status-title" className="workspace">
      <header className="workspace-header">
        <div><p className="eyebrow">Apistra administration</p><strong>{session.administrator.username}</strong></div>
        <AdministratorMenu onInstallationStatus={() => undefined} onSignOut={onSignOut} />
      </header>
      <nav aria-label="Project navigation"><a href="/">Overview</a><a href="/audit">Audit</a></nav>
      {content}
    </section>
  );
}

export { bootstrapAdministrator, validateCredentials } from "./internal/identity-client";
