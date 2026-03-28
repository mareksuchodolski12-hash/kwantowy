'use client';

import ExperimentForm from '@/components/ExperimentForm';

export default function SubmitExperimentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">New Experiment</h2>
        <p className="text-sm text-text-muted mt-1">Configure and submit a quantum circuit experiment</p>
      </div>
      <div className="glass rounded-xl glow-border p-6">
        <ExperimentForm />
      </div>
    </div>
  );
}
