import { AdministrationApp } from "../../../features/administration/public";

export default async function ProjectPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <main className="installation-shell"><AdministrationApp requestedProjectId={projectId} /></main>;
}
