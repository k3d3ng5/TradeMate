export default async (request) => {
  const origin = process.env.TRADEMATE_API_ORIGIN;
  if (!origin) {
    return Response.json({ detail: "TradeMate API is not configured yet." }, { status: 503 });
  }

  let destination;
  try {
    destination = new URL(request.url);
    const apiOrigin = new URL(origin);
    destination.protocol = apiOrigin.protocol;
    destination.host = apiOrigin.host;
  } catch {
    return Response.json({ detail: "TradeMate API configuration is invalid." }, { status: 503 });
  }

  const headers = new Headers(request.headers);
  for (const name of ["host", "content-length", "connection", "accept-encoding"]) headers.delete(name);
  const options = {
    method: request.method,
    headers,
    redirect: "manual",
    signal: AbortSignal.timeout(55_000),
  };
  if (request.method !== "GET" && request.method !== "HEAD") options.body = await request.arrayBuffer();

  try {
    const upstream = await fetch(destination, options);
    const responseHeaders = new Headers(upstream.headers);
    for (const name of ["content-encoding", "content-length", "transfer-encoding", "connection"]) responseHeaders.delete(name);
    responseHeaders.set("cache-control", "no-store");
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch {
    return Response.json({ detail: "TradeMate API is temporarily unavailable." }, { status: 502 });
  }
};

export const config = { path: "/api/*" };
