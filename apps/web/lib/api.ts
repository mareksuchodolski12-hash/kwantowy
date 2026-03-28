// In production, requests go through the server-side proxy (/api/qcp/) which
// injects the API key server-side.  The NEXT_PUBLIC_API_KEY fallback only
// applies during local development when hitting the backend directly.
const IS_SERVER = typeof window === 'undefined';
const DIRECT_URL = process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const BASE_URL = IS_SERVER ? DIRECT_URL : '/api/qcp';
const SERVER_API_KEY = process.env.QCP_API_KEY ?? process.env.NEXT_PUBLIC_API_KEY ?? '';

function authHeaders(): HeadersInit {
  // On the server (SSR), attach key directly; on the client, the proxy handles it.
  if (IS_SERVER && SERVER_API_KEY) {
    return { 'X-API-Key': SERVER_API_KEY };
  }
  return {};
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
  is_simulator: boolean;
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
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `submit failed (${res.status})`);
  }
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
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `job fetch failed (${res.status})`);
  }
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

export interface ResultComparison {
  experiment_name: string;
  results: ExecutionResult[];
  fidelity_scores: Record<string, number>;
  distribution_distances: Record<string, number>;
  total_duration_ms: number;
}

export async function compareResults(
  experimentName: string,
  jobIds: string[],
  referenceDistribution?: Record<string, number>,
): Promise<{ comparison: ResultComparison }> {
  const body: Record<string, unknown> = {
    experiment_name: experimentName,
    job_ids: jobIds,
  };
  if (referenceDistribution) {
    body.reference_distribution = referenceDistribution;
  }
  const res = await fetch(`${BASE_URL}/v1/results/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `compare failed (${res.status})`);
  }
  return res.json();
}
