import Link from 'next/link';
import type { Experiment, Job } from '@/lib/api';
import StatusBadge from './StatusBadge';
import ProviderBadge from './ProviderBadge';

interface ExperimentRow {
  experiment: Experiment;
  job: Job | undefined;
}

export default function ExperimentTable({ rows }: { rows: ExperimentRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-gray-500 py-8 text-center">
        No experiments yet.{' '}
        <Link href="/experiments/new" className="text-indigo-600 hover:underline">
          Submit one
        </Link>
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shots</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map(({ experiment, job }) => (
            <tr key={experiment.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm">
                <Link
                  href={`/experiments/${experiment.id}`}
                  className="text-indigo-600 hover:underline font-medium"
                >
                  {experiment.name}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm">
                {job ? <ProviderBadge provider={job.provider} /> : <span className="text-gray-400">—</span>}
              </td>
              <td className="px-4 py-3 text-sm">
                {job ? <StatusBadge status={job.status} /> : <span className="text-gray-400">—</span>}
              </td>
              <td className="px-4 py-3 text-sm text-gray-700">{experiment.circuit.shots}</td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {new Date(experiment.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
