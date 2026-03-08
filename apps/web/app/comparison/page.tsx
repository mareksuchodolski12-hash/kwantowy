import { getResult, listJobs } from '@/lib/api';

export default async function ComparisonPage() {
  const { jobs } = await listJobs();
  const completed = jobs.filter((job) => job.status === 'succeeded').slice(0, 10);
  const rows = await Promise.all(
    completed.map(async (job) => ({
      job,
      result: await getResult(job.id)
    }))
  );

  return (
    <section>
      <h2>Local vs Remote Comparison</h2>
      <p>Comparison view across succeeded runs grouped by provider.</p>
      <table>
        <thead>
          <tr>
            <th>Job</th>
            <th>Provider</th>
            <th>Backend</th>
            <th>Duration (ms)</th>
            <th>Shots</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ job, result }) => (
            <tr key={job.id}>
              <td>{job.id.slice(0, 8)}</td>
              <td>{job.provider}</td>
              <td>{result?.result?.backend ?? '-'}</td>
              <td>{result?.result?.duration_ms ?? '-'}</td>
              <td>{result?.result?.shots ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
