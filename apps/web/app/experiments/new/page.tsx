'use client';

import ExperimentForm from '@/components/ExperimentForm';

export default function SubmitExperimentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">New Experiment</h2>
        <p className="text-sm text-gray-500 mt-1">Configure and submit a quantum circuit experiment</p>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <ExperimentForm />
      </div>
    </div>
  );
}
