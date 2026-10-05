import { ToolsApp } from "../../../../features/policies/public";

export default async function ToolsPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <main className="installation-shell"><ToolsApp projectId={projectId} /></main>;
}
