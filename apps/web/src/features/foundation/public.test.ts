import { describe, expect, it } from "vitest";

import { getDeploymentMarker, getFoundationStatus } from "./public";

describe("foundation public contract", () => {
  it("exposes the retained foundation status", () => {
    expect(getFoundationStatus()).toBe("architecture-foundation");
  });

  it("creates a deployment marker without secrets", () => {
    expect(
      getDeploymentMarker({
        NEXT_PUBLIC_APISTRA_VERSION: "0.0.1",
        NEXT_PUBLIC_APISTRA_COMMIT: "abc123",
        NEXT_PUBLIC_APISTRA_ENVIRONMENT: "test"
      })
    ).toEqual({ service: "web", version: "0.0.1", commit: "abc123", environment: "test" });
  });
});
