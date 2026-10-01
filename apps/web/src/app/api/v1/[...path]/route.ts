import type { NextRequest } from "next/server";

const REQUEST_HEADERS = ["content-type", "cookie", "x-correlation-id", "x-csrf-token"];

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const apiBase = (process.env.APISTRA_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  const suffix = path.map(encodeURIComponent).join("/");
  const headers = new Headers();
  for (const name of REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const upstream = await fetch(`${apiBase}/api/v1/${suffix}`, {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      redirect: "manual"
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: upstream.headers
    });
  } catch {
    return Response.json(
      {
        type: "https://apistra.dev/problems/upstream-unavailable",
        title: "upstream_unavailable",
        detail: "The local API is not available. Try again after it is ready."
      },
      { status: 502 }
    );
  }
}

export const dynamic = "force-dynamic";
export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
