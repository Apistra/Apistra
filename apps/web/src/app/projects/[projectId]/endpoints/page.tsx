import { EndpointCatalogueApp } from "../../../../features/catalog/endpoints";

export default async function EndpointCataloguePage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <main className="installation-shell"><EndpointCatalogueApp projectId={projectId} /></main>;
}
