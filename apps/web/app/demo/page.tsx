'use client';

import { useState } from 'react';
import { submitExperiment, getResult, getJob, type Provider } from '@/lib/api';
import ResultChart from '@/components/ResultChart';

const CIRCUITS: { label: string; name: string; qasm: string }[] = [
  {
    label: 'Bell State',
    name: 'bell-state-demo',
    qasm: 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q[0] -> c[0]; measure q[1] -> c[1];',
  },
  {
    label: 'GHZ State (3 qubits)',
    name: 'ghz-state-demo',
    qasm: 'OPENQASM 2.0;\ninclude "qelib1.inc";\n\nqreg q[3];\ncreg c[3];\n\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\n\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];',
  },
  {
    label: 'Grover (2-qubit)',
    name: 'grover-demo',
    qasm: 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; h q[1]; cz q[0],q[1]; h q[0]; h q[1]; x q[0]; x q[1]; h q[1]; cx q[0],q[1]; h q[1]; x q[0]; x q[1]; h q[0]; h q[1]; measure q[0] -> c[0]; measure q[1] -> c[1];',
  },
  {
    label: 'Deutsch-Jozsa',
    name: 'deutsch-jozsa-demo',
    qasm: 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[1]; x q[1]; h q[0]; h q[1]; cx q[0],q[1]; h q[0]; measure q[0] -> c[0];',
  },
];

export default function DemoPage() {
  const [selected, setSelected] = useState(0);
  const [running, setRunning] = useState(false);
  const [counts, setCounts] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobInfo, setJobInfo] = useState<{ id: string; status: string } | null>(null);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    setCounts(null);
    setJobInfo(null);

    const circuit = CIRCUITS[selected];
    try {
      const data = await submitExperiment({
        name: circuit.name,
        provider: 'local_simulator' as Provider,
        circuit: { qasm: circuit.qasm, shots: 1024 },
        retry_policy: { max_attempts: 3, timeout_seconds: 120 },
      });

      const jobId = data.job.id;
      setJobInfo({ id: jobId, status: data.job.status });

      // Poll for result
      for (let i = 0; i < 30; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        const job = await getJob(jobId);
        setJobInfo({ id: jobId, status: job.status });
        if (job.status === 'succeeded') {
          const res = await getResult(jobId);
          if (res) {
            setCounts(res.result.counts);
          }
          break;
        }
        if (job.status === 'failed') {
          setError('Job failed.');
          break;
        }
        if (i === 29) {
          setError('Timed out waiting for result. The job may still be running — check the Runs page.');
          break;
        }
      }
    } catch (err: unknown) {
      if (err instanceof TypeError) {
        setError('Failed to connect to the API server. Is it running?');
      } else if (err instanceof Error && err.message) {
        setError(`Experiment error: ${err.message}`);
      } else {
        setError('An unexpected error occurred.');
      }
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">Interactive Demo</h2>
        <p className="text-sm text-text-muted mt-1">
          Run a quantum circuit with one click and see the results.
        </p>
      </div>

      <div className="glass rounded-xl glow-border p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">Select Circuit</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {CIRCUITS.map((c, idx) => (
              <button
                key={c.name}
                onClick={() => { setSelected(idx); setCounts(null); setJobInfo(null); }}
                className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                  selected === idx
                    ? 'border-accent/40 bg-accent/10 text-accent'
                    : 'border-muted/40 hover:border-muted/60 text-text-secondary'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">QASM</label>
          <pre className="bg-abyss border border-muted/40 rounded-lg p-3 text-xs font-mono text-accent/70 overflow-x-auto whitespace-pre-wrap">
            {CIRCUITS[selected].qasm}
          </pre>
        </div>

        <button
          onClick={handleRun}
          disabled={running}
          className="w-full btn-primary py-3"
        >
          {running ? 'Running…' : `Run ${CIRCUITS[selected].label}`}
        </button>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded text-sm">{error}</div>
        )}

        {jobInfo && (
          <div className="text-sm text-text-secondary">
            Job <span className="font-mono">{jobInfo.id.slice(0, 8)}</span> — Status:{' '}
            <span className="font-semibold">{jobInfo.status}</span>
          </div>
        )}

        {counts && (
          <div className="pt-2">
            <ResultChart counts={counts} title="Measurement Results (1024 shots)" />
          </div>
        )}
      </div>
    </div>
  );
}
