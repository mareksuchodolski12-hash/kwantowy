'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getExperiment, listJobs, getResult, type Experiment, type Job, type ExecutionResult } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import ProviderBadge from '@/components/ProviderBadge';
import ResultChart from '@/components/ResultChart';

export default function ExperimentDetailPage() {
  const params = useParams<{ id: string }>();
  const experimentId = params.id;

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [exp, { jobs }] = await Promise.all([
        getExperiment(experimentId),
        listJobs(),
      ]);
      setExperiment(exp);
      const matched = jobs.find((j) => j.experiment_id === experimentId);
      if (matched) {
        setJob(matched);
        if (matched.status === 'succeeded') {
          const res = await getResult(matched.id);
          if (res) setResult(res.result);
        }
      }
    } finally {
      setLoading(false);
    }
  }, [experimentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!job || job.status === 'succeeded' || job.status === 'failed') return;
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [job, fetchData]);

  if (loading) {
    return <p className="text-text-muted py-8 text-center">Loading experiment…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/experiments" className="text-sm text-accent hover:underline">
            ← Back to Experiments
          </Link>
          <h2 className="text-2xl font-bold text-text-primary mt-1">
            {experiment?.name ?? 'Experiment'}
          </h2>
          {experiment?.description && (
            <p className="text-sm text-text-muted mt-1">{experiment.description}</p>
          )}
        </div>
        {job && <StatusBadge status={job.status} />}
      </div>

      {experiment && (
        <div className="glass rounded-xl glow-border p-6 space-y-4">
          <h3 className="text-lg font-semibold text-text-primary">Experiment Details</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-text-muted uppercase">Shots</p>
              <p className="text-sm font-medium">{experiment.circuit.shots}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Created</p>
              <p className="text-sm font-medium">{new Date(experiment.created_at).toLocaleString()}</p>
            </div>
            {job && (
              <>
                <div>
                  <p className="text-xs text-text-muted uppercase">Provider</p>
                  <ProviderBadge provider={job.provider} />
                </div>
                <div>
                  <p className="text-xs text-text-muted uppercase">Attempts</p>
                  <p className="text-sm font-medium">{job.attempts}</p>
                </div>
              </>
            )}
          </div>
          <div>
            <p className="text-xs text-text-muted uppercase mb-1">QASM Circuit</p>
            <pre className="bg-abyss border border-muted/40 rounded-lg p-3 text-xs font-mono text-text-secondary overflow-x-auto whitespace-pre-wrap">
              {experiment.circuit.qasm}
            </pre>
          </div>
        </div>
      )}

      {job && (
        <div className="glass rounded-xl glow-border p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-3">Job Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-text-muted uppercase">Status</p>
              <StatusBadge status={job.status} />
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Provider</p>
              <ProviderBadge provider={job.provider} />
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Correlation ID</p>
              <p className="text-sm font-medium text-text-secondary truncate">{job.correlation_id}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Updated</p>
              <p className="text-sm font-medium">{new Date(job.updated_at).toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="glass rounded-xl glow-border p-6 space-y-4">
          <h3 className="text-lg font-semibold text-text-primary">Execution Result</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-xs text-text-muted uppercase">Backend</p>
              <p className="text-sm font-medium">{result.backend}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Shots</p>
              <p className="text-sm font-medium">{result.shots}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Duration</p>
              <p className="text-sm font-medium">{result.duration_ms} ms</p>
            </div>
            <div>
              <p className="text-xs text-text-muted uppercase">Completed</p>
              <p className="text-sm font-medium">{new Date(result.completed_at).toLocaleString()}</p>
            </div>
          </div>
          <ResultChart counts={result.counts} title="Measurement Counts" />
        </div>
      )}

      {job && !result && job.status !== 'succeeded' && job.status !== 'failed' && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
          <p className="text-amber-400 text-sm">
            Job is {job.status}. Results will appear automatically when execution completes.
          </p>
        </div>
      )}
    </div>
  );
}
