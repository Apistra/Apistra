import { foundationStatus } from "./internal/foundation-status";

export function getFoundationStatus(): string {
  return foundationStatus;
}

export interface DeploymentMarker {
  service: "web";
  version: string;
  commit: string;
  environment: string;
}

export function getDeploymentMarker(
  environment: Record<string, string | undefined> = process.env
): DeploymentMarker {
  return {
    service: "web",
    version: environment.APISTRA_VERSION ?? environment.NEXT_PUBLIC_APISTRA_VERSION ?? "0.0.0-dev",
    commit: environment.APISTRA_COMMIT ?? environment.NEXT_PUBLIC_APISTRA_COMMIT ?? "unknown",
    environment:
      environment.APISTRA_ENVIRONMENT ?? environment.NEXT_PUBLIC_APISTRA_ENVIRONMENT ?? "local"
  };
}
