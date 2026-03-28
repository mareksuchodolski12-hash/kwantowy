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
          <h2 className="text-2xl font-bold text-text-primary">Experiments</h2>
          <p className="text-sm text-text-muted mt-1">Browse and monitor quantum experiments</p>
        </div>
        <a href="/experiments/new" className="btn-primary">
          New Experiment
        </a>
      </div>
      <div className="glass rounded-xl glow-border">
        <ExperimentTable rows={rows} />
      </div>
    </div>
  );
}
