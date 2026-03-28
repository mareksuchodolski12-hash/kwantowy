'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { getJob, getResult, type Job, type ExecutionResult } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import ProviderBadge from '@/components/ProviderBadge';
import ResultChart from '@/components/ResultChart';

export default function RunDetailsPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;

  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const j = await getJob(jobId);
      setJob(j);
      if (j.status === 'succeeded') {
        const res = await getResult(jobId);
        if (res) setResult(res.result);
      }
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!job || job.status === 'succeeded' || job.status === 'failed') return;
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [job, fetchData]);

  if (loading) {
    return <p className="text-text-muted py-8 text-center">Loading run details…</p>;
  }

  if (!job) {
    return <p className="text-red-500 py-8 text-center">Job not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">Run Details</h2>
        <p className="text-sm text-text-muted mt-1">Job ID: {job.id}</p>
      </div>

      <div className="glass rounded-xl glow-border p-6">
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
            <p className="text-xs text-text-muted uppercase">Attempts</p>
            <p className="text-sm font-medium">{job.attempts}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted uppercase">Updated</p>
            <p className="text-sm font-medium">{new Date(job.updated_at).toLocaleString()}</p>
          </div>
        </div>
      </div>

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

      {!result && job.status !== 'succeeded' && job.status !== 'failed' && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
          <p className="text-amber-400 text-sm">
            ⏳ Job is {job.status}. Results will appear automatically when execution completes.
          </p>
        </div>
      )}
    </div>
  );
}
