'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  listJobs,
  listExperiments,
  getResult,
  compareResults,
  type Job,
  type Experiment,
  type ExecutionResult,
  type ResultComparison,
} from '@/lib/api';
import ProviderBadge from '@/components/ProviderBadge';
import ResultChart from '@/components/ResultChart';

interface ComparisonRow {
  job: Job;
  result: ExecutionResult;
  experimentName: string;
  selected: boolean;
}

export default function ComparisonPage() {
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [{ jobs }, { experiments }] = await Promise.all([listJobs(), listExperiments()]);
      const expMap = new Map(experiments.map((e) => [e.id, e]));
      const succeeded = jobs.filter((j) => j.status === 'succeeded').slice(0, 20);
      const withResults = await Promise.all(
        succeeded.map(async (job) => {
          const res = await getResult(job.id);
          if (!res) return null;
          const exp = expMap.get(job.experiment_id);
          return { job, result: res.result, experimentName: exp?.name ?? job.id.slice(0, 8), selected: false };
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
  const [comparison, setComparison] = useState<ResultComparison | null>(null);
  const [comparing, setComparing] = useState(false);

  const handleCompare = async () => {
    if (selected.length < 2) return;
    setComparing(true);
    setComparison(null);
    try {
      const resp = await compareResults(
        selected[0].experimentName,
        selected.map((r) => r.job.id),
      );
      setComparison(resp.comparison);
    } catch {
      // fall through — comparison is optional enhancement
    } finally {
      setComparing(false);
    }
  };

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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Experiment</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Backend</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration (ms)</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shots</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map(({ job, result, experimentName, selected: sel }) => (
              <tr
                key={job.id}
                className={`cursor-pointer transition-colors ${sel ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}
                onClick={() => toggleRow(job.id)}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={sel}
                    readOnly
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 pointer-events-none"
                  />
                </td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{experimentName}</td>
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
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              Comparing {selected.length} result{selected.length > 1 ? 's' : ''}
            </h3>
            {selected.length >= 2 && (
              <button
                onClick={handleCompare}
                disabled={comparing}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {comparing ? 'Comparing…' : 'Run Statistical Comparison'}
              </button>
            )}
          </div>

          {comparison && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 space-y-3">
              <h4 className="text-sm font-semibold text-gray-800">Statistical Summary</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {Object.keys(comparison.fidelity_scores).length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 uppercase mb-1">Fidelity Scores</p>
                    {Object.entries(comparison.fidelity_scores).map(([provider, score]) => (
                      <div key={provider} className="flex justify-between">
                        <span className="text-gray-700">{provider}</span>
                        <span className="font-medium">{(score * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                )}
                {Object.keys(comparison.distribution_distances).length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 uppercase mb-1">Distribution Distances (KL)</p>
                    {Object.entries(comparison.distribution_distances).map(([provider, dist]) => (
                      <div key={provider} className="flex justify-between">
                        <span className="text-gray-700">{provider}</span>
                        <span className="font-medium">{dist.toFixed(4)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-xs text-gray-500">
                Total duration: {comparison.total_duration_ms} ms
              </p>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {selected.map(({ job, result, experimentName }) => (
              <div key={job.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800">{experimentName}</span>
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
