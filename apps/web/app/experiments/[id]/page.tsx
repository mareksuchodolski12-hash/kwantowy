'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { listJobs, getResult, type Job, type ExecutionResult } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import ProviderBadge from '@/components/ProviderBadge';
import ResultChart from '@/components/ResultChart';

export default function ExperimentDetailPage() {
  const params = useParams<{ id: string }>();
  const experimentId = params.id;

  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const { jobs } = await listJobs();
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
    return <p className="text-gray-500 py-8 text-center">Loading experiment…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Experiment Detail</h2>
        <p className="text-sm text-gray-500 mt-1">ID: {experimentId}</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">Job Status</h3>
        {job ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500 uppercase">Status</p>
              <StatusBadge status={job.status} />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Provider</p>
              <ProviderBadge provider={job.provider} />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Attempts</p>
              <p className="text-sm font-medium">{job.attempts}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Updated</p>
              <p className="text-sm font-medium">{new Date(job.updated_at).toLocaleString()}</p>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No job found for this experiment.</p>
        )}
      </div>

      {result && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Execution Result</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-xs text-gray-500 uppercase">Backend</p>
              <p className="text-sm font-medium">{result.backend}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Shots</p>
              <p className="text-sm font-medium">{result.shots}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Duration</p>
              <p className="text-sm font-medium">{result.duration_ms} ms</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Completed</p>
              <p className="text-sm font-medium">{new Date(result.completed_at).toLocaleString()}</p>
            </div>
          </div>
          <ResultChart counts={result.counts} title="Measurement Counts" />
        </div>
      )}

      {job && !result && job.status !== 'succeeded' && job.status !== 'failed' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            ⏳ Job is {job.status}. Results will appear automatically when execution completes.
          </p>
        </div>
      )}
    </div>
  );
}
