const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? '';

function authHeaders(): HeadersInit {
  return API_KEY ? { 'X-API-Key': API_KEY } : {};
}

export type Provider = 'local_simulator' | 'ibm_runtime' | 'ionq' | 'rigetti' | 'simulator_aer';

export interface Experiment {
  id: string;
  name: string;
  description: string | null;
  circuit: { qasm: string; shots: number };
  created_at: string;
}

export interface Job {
  id: string;
  experiment_id: string;
  status: string;
  provider: Provider;
  attempts: number;
  correlation_id: string;
  created_at: string;
  updated_at: string;
}

export interface ExecutionResult {
  job_id: string;
  provider: Provider;
  backend: string;
  counts: Record<string, number>;
  shots: number;
  duration_ms: number;
  completed_at: string;
  remote_run_id: string | null;
}

export interface ProviderCapabilities {
  provider: Provider;
  max_qubits: number;
  supports_mid_circuit_measurement: boolean;
  estimated_cost_per_shot_usd: number;
  avg_queue_time_seconds: number;
  estimated_fidelity: number;
}

export interface SubmitPayload {
  name: string;
  description?: string;
  provider: Provider;
  circuit: { qasm: string; shots: number };
  retry_policy: { max_attempts: number; timeout_seconds: number };
}

export async function submitExperiment(payload: SubmitPayload): Promise<{ experiment: Experiment; job: Job }> {
  const res = await fetch(`${BASE_URL}/v1/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('submit failed');
  return res.json();
}

export async function listExperiments(): Promise<{ experiments: Experiment[] }> {
  const res = await fetch(`${BASE_URL}/v1/experiments`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('list experiments failed');
  return res.json();
}

export async function listJobs(): Promise<{ jobs: Job[] }> {
  const res = await fetch(`${BASE_URL}/v1/jobs`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('list failed');
  return res.json();
}

export async function getJob(id: string): Promise<Job> {
  const res = await fetch(`${BASE_URL}/v1/jobs/${id}`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('job fetch failed');
  return res.json();
}

export async function getResult(id: string): Promise<{ result: ExecutionResult } | null> {
  const res = await fetch(`${BASE_URL}/v1/results/${id}`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function getExperiment(id: string): Promise<Experiment> {
  const res = await fetch(`${BASE_URL}/v1/experiments/${encodeURIComponent(id)}`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('experiment fetch failed');
  return res.json();
}

export async function listProviders(): Promise<ProviderCapabilities[]> {
  const res = await fetch(`${BASE_URL}/v1/providers`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('list providers failed');
  return res.json();
}
