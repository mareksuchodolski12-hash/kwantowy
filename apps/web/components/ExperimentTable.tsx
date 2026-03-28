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
      <p className="text-text-muted py-8 text-center">
        No experiments yet.{' '}
        <Link href="/experiments/new" className="text-accent hover:underline">
          Submit one
        </Link>
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-muted/40">
        <thead>
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">Provider</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">Shots</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-muted/20">
          {rows.map(({ experiment, job }) => (
            <tr key={experiment.id} className="hover:bg-accent/[0.03] transition-colors">
              <td className="px-4 py-3 text-sm">
                <Link
                  href={`/experiments/${experiment.id}`}
                  className="text-accent hover:text-accent-dim font-medium transition-colors"
                >
                  {experiment.name}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm">
                {job ? <ProviderBadge provider={job.provider} /> : <span className="text-text-muted">—</span>}
              </td>
              <td className="px-4 py-3 text-sm">
                {job ? <StatusBadge status={job.status} /> : <span className="text-text-muted">—</span>}
              </td>
              <td className="px-4 py-3 text-sm font-mono text-text-secondary">{experiment.circuit.shots}</td>
              <td className="px-4 py-3 text-sm text-text-muted">
                {new Date(experiment.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
