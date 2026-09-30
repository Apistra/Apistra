import { NextResponse } from "next/server";

import { getDeploymentMarker } from "../../../features/foundation/public";

export function GET() {
  return NextResponse.json({ status: "ready", deployment: getDeploymentMarker() });
}
