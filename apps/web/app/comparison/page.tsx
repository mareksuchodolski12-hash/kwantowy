'use client';

import { useEffect, useState, useCallback } from 'react';
import { listJobs, getResult, type Job, type ExecutionResult } from '@/lib/api';
import ProviderBadge from '@/components/ProviderBadge';
import ResultChart from '@/components/ResultChart';

interface ComparisonRow {
  job: Job;
  result: ExecutionResult;
  selected: boolean;
}

export default function ComparisonPage() {
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const { jobs } = await listJobs();
      const succeeded = jobs.filter((j) => j.status === 'succeeded').slice(0, 20);
      const withResults = await Promise.all(
        succeeded.map(async (job) => {
          const res = await getResult(job.id);
          return res ? { job, result: res.result, selected: false } : null;
        }),
      );
      setRows(withResults.filter((r): r is ComparisonRow => r !== null));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const toggleRow = (jobId: string) => {
    setRows((prev) => prev.map((r) => (r.job.id === jobId ? { ...r, selected: !r.selected } : r)));
  };

  const selected = rows.filter((r) => r.selected);

  if (loading) {
    return <p className="text-gray-500 py-8 text-center">Loading comparison data…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Result Comparison</h2>
        <p className="text-sm text-gray-500 mt-1">
          Select experiments to compare their results across providers
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Select</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Backend</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration (ms)</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shots</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map(({ job, result, selected: sel }) => (
              <tr
                key={job.id}
                className={`cursor-pointer transition-colors ${sel ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}
                onClick={() => toggleRow(job.id)}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={sel}
                    onChange={() => toggleRow(job.id)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                </td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{job.id.slice(0, 8)}</td>
                <td className="px-4 py-3 text-sm">
                  <ProviderBadge provider={job.provider} />
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{result.backend}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{result.duration_ms}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{result.shots}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No succeeded runs available for comparison.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">
            Comparing {selected.length} result{selected.length > 1 ? 's' : ''}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {selected.map(({ job, result }) => (
              <div key={job.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800">{job.id.slice(0, 8)}</span>
                  <ProviderBadge provider={job.provider} />
                </div>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">Duration</p>
                    <p className="font-medium">{result.duration_ms} ms</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Shots</p>
                    <p className="font-medium">{result.shots}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Backend</p>
                    <p className="font-medium">{result.backend}</p>
                  </div>
                </div>
                <ResultChart counts={result.counts} title="Measurement Distribution" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
