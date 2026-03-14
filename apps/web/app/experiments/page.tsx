import { listExperiments, listJobs } from '@/lib/api';
import ExperimentTable from '@/components/ExperimentTable';

export const dynamic = 'force-dynamic';

export default async function ExperimentsPage() {
  const [expData, jobData] = await Promise.all([listExperiments(), listJobs()]);
  const jobsByExperiment = new Map(jobData.jobs.map((j) => [j.experiment_id, j]));
  const rows = expData.experiments.map((exp) => ({
    experiment: exp,
    job: jobsByExperiment.get(exp.id),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Experiments</h2>
          <p className="text-sm text-gray-500 mt-1">Browse and monitor quantum experiments</p>
        </div>
        <a
          href="/experiments/new"
          className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          New Experiment
        </a>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <ExperimentTable rows={rows} />
      </div>
    </div>
  );
}
