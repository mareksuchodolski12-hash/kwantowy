'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { submitExperiment, type Provider } from '@/lib/api';

const SAMPLE_QASM =
  'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q[0] -> c[0]; measure q[1] -> c[1];';

const PROVIDERS: { value: Provider; label: string }[] = [
  { value: 'local_simulator', label: 'Local Simulator' },
  { value: 'ibm_runtime', label: 'IBM Runtime' },
  { value: 'simulator_aer', label: 'Aer Simulator' },
];

export default function ExperimentForm() {
  const router = useRouter();
  const [name, setName] = useState('bell-state-demo');
  const [description, setDescription] = useState('Bell state experiment');
  const [provider, setProvider] = useState<Provider>('local_simulator');
  const [qasm, setQasm] = useState(SAMPLE_QASM);
  const [shots, setShots] = useState(1024);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const data = await submitExperiment({
        name,
        description: description || undefined,
        provider,
        circuit: { qasm, shots },
        retry_policy: { max_attempts: 3, timeout_seconds: 120 },
      });
      router.push(`/experiments/${data.experiment.id}`);
    } catch {
      setError('Failed to submit experiment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Experiment Name</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="my-experiment"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="Optional description"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as Provider)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Shots</label>
          <input
            type="number"
            min={1}
            max={10000}
            value={shots}
            onChange={(e) => setShots(Number(e.target.value))}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">QASM Circuit</label>
        <textarea
          rows={8}
          value={qasm}
          onChange={(e) => setQasm(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="OPENQASM 2.0; ..."
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="bg-indigo-600 text-white px-6 py-2.5 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {submitting ? 'Submitting…' : 'Submit Experiment'}
      </button>
    </form>
  );
}
