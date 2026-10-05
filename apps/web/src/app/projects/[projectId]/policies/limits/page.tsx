import { LimitsApp } from "../../../../../features/policies/limits";

export default async function LimitsPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <main className="installation-shell"><LimitsApp projectId={projectId} /></main>;
}
