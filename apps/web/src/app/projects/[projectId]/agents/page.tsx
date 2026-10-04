import { AgentVersionsApp } from "../../../../features/agents/public";

export default async function AgentVersionsPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <main className="installation-shell"><AgentVersionsApp projectId={projectId} /></main>;
}
