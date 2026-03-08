import Link from 'next/link';
import { listJobs } from '@/lib/api';

export default async function RunsPage() {
  const { jobs } = await listJobs();
  return (
    <section>
      <h2>Run History</h2>
      <table>
        <thead>
          <tr>
            <th>Job</th>
            <th>Provider</th>
            <th>Status</th>
            <th>Attempts</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>
                <Link href={`/runs/${job.id}`}>{job.id.slice(0, 8)}</Link>
              </td>
              <td>{job.provider}</td>
              <td>{job.status}</td>
              <td>{job.attempts}</td>
              <td>{new Date(job.updated_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
