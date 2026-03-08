import { getJob, getResult } from '@/lib/api';

export default async function RunDetailsPage({ params }: { params: { id: string } }) {
  const job = await getJob(params.id);
  const result = await getResult(params.id);

  return (
    <section>
      <h2>Run Details</h2>
      <p><strong>Job:</strong> {job.id}</p>
      <p><strong>Provider:</strong> {job.provider}</p>
      <p><strong>Status:</strong> {job.status}</p>
      <p><strong>Attempts:</strong> {job.attempts}</p>
      <h3>Result</h3>
      {result ? <pre>{JSON.stringify(result, null, 2)}</pre> : <p>Result not ready.</p>}
    </section>
  );
}
