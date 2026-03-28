import Link from 'next/link';
import { listJobs } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import ProviderBadge from '@/components/ProviderBadge';

export const dynamic = 'force-dynamic';

export default async function RunsPage() {
  const { jobs } = await listJobs();
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">Run History</h2>
        <p className="text-sm text-text-muted mt-1">All quantum job executions</p>
      </div>
      <div className="glass rounded-xl glow-border overflow-x-auto">
        <table className="min-w-full divide-y divide-muted/40">
          <thead className="bg-panel/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Job</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Provider</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Attempts</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-muted/20">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-accent/[0.03] transition-colors">
                <td className="px-4 py-3 text-sm">
                  <Link href={`/runs/${job.id}`} className="text-accent hover:underline font-medium">
                    {job.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm">
                  <ProviderBadge provider={job.provider} />
                </td>
                <td className="px-4 py-3 text-sm">
                  <StatusBadge status={job.status} />
                </td>
                <td className="px-4 py-3 text-sm text-text-secondary">{job.attempts}</td>
                <td className="px-4 py-3 text-sm text-text-muted">{new Date(job.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
