import { getDeploymentMarker } from "../features/foundation/public";

export default function Home() {
  const marker = getDeploymentMarker();
  return (
    <main>
      <section aria-labelledby="title" className="status-card">
        <p className="eyebrow">CAP-00 · Bootstrap</p>
        <h1 id="title">Apistra is ready for construction.</h1>
        <p className="summary">
          This health-only shell proves that the web, API, worker, packaging, and recovery
          paths work before business capabilities are introduced.
        </p>
        <dl>
          <div><dt>Status</dt><dd><span className="indicator" aria-hidden="true" />Ready</dd></div>
          <div><dt>Version</dt><dd>{marker.version}</dd></div>
          <div><dt>Commit</dt><dd>{marker.commit}</dd></div>
          <div><dt>Environment</dt><dd>{marker.environment}</dd></div>
        </dl>
      </section>
    </main>
  );
}
