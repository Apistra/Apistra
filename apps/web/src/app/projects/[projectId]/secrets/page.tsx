import { SecretReferencesApp } from "../../../../features/catalog/public";

export default async function SecretReferencesPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <main className="installation-shell"><SecretReferencesApp projectId={projectId} /></main>;
}
