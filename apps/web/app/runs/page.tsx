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
        <h2 className="text-2xl font-bold text-gray-900">Run History</h2>
        <p className="text-sm text-gray-500 mt-1">All quantum job executions</p>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Attempts</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Updated</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm">
                  <Link href={`/runs/${job.id}`} className="text-indigo-600 hover:underline font-medium">
                    {job.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm">
                  <ProviderBadge provider={job.provider} />
                </td>
                <td className="px-4 py-3 text-sm">
                  <StatusBadge status={job.status} />
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{job.attempts}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{new Date(job.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
