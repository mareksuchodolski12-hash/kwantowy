import { NextRequest, NextResponse } from 'next/server';

/**
 * Server-side proxy that forwards requests to the QCP API.
 * The API key is kept in a server-only env var (QCP_API_KEY) and
 * never shipped to the browser, eliminating the NEXT_PUBLIC_API_KEY leak.
 */

const BACKEND_URL = process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.QCP_API_KEY ?? process.env.NEXT_PUBLIC_API_KEY ?? '';

async function proxyRequest(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/');
  const url = `${BACKEND_URL}/${path}${req.nextUrl.search}`;

  const headers = new Headers(req.headers);
  if (API_KEY) {
    headers.set('X-API-Key', API_KEY);
  }
  // Remove host header to avoid backend confusion
  headers.delete('host');

  const res = await fetch(url, {
    method: req.method,
    headers,
    body: req.method !== 'GET' && req.method !== 'HEAD' ? await req.text() : undefined,
  });

  const body = await res.arrayBuffer();
  return new NextResponse(body, {
    status: res.status,
    statusText: res.statusText,
    headers: {
      'content-type': res.headers.get('content-type') ?? 'application/json',
    },
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;
