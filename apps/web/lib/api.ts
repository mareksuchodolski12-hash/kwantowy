const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? '';

function authHeaders(): HeadersInit {
  return API_KEY ? { 'X-API-Key': API_KEY } : {};
}

export type Provider = 'local_simulator' | 'ibm_runtime';

export interface Job {
  id: string;
  experiment_id: string;
  status: string;
  provider: Provider;
  attempts: number;
  created_at: string;
  updated_at: string;
}

export interface SubmitPayload {
  name: string;
  description?: string;
  provider: Provider;
  circuit: { qasm: string; shots: number };
  retry_policy: { max_attempts: number; timeout_seconds: number };
}

export async function submitJob(payload: SubmitPayload) {
  const res = await fetch(`${BASE_URL}/v1/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('submit failed');
  return res.json();
}

export async function listJobs(): Promise<{ jobs: Job[] }> {
  const res = await fetch(`${BASE_URL}/v1/jobs`, {
    cache: 'no-store',
    headers: authHeaders()
  });
  if (!res.ok) throw new Error('list failed');
  return res.json();
}

export async function getJob(id: string): Promise<Job> {
  const res = await fetch(`${BASE_URL}/v1/jobs/${id}`, {
    cache: 'no-store',
    headers: authHeaders()
  });
  if (!res.ok) throw new Error('job fetch failed');
  return res.json();
}

export async function getResult(id: string) {
  const res = await fetch(`${BASE_URL}/v1/results/${id}`, {
    cache: 'no-store',
    headers: authHeaders()
  });
  if (!res.ok) return null;
  return res.json();
}
