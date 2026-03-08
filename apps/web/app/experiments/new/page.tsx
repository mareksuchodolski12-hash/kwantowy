'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { submitJob, type Provider } from '@/lib/api';

const SAMPLE_QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];';

export default function SubmitExperimentPage() {
  const router = useRouter();
  const [name, setName] = useState('phase3-demo');
  const [description, setDescription] = useState('portfolio walkthrough run');
  const [provider, setProvider] = useState<Provider>('local_simulator');
  const [qasm, setQasm] = useState(SAMPLE_QASM);
  const [shots, setShots] = useState(128);

  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault();
        const data = await submitJob({
          name,
          description,
          provider,
          circuit: { qasm, shots },
          retry_policy: { max_attempts: 2, timeout_seconds: 60 }
        });
        router.push(`/runs/${data.job.id}`);
      }}
    >
      <h2>Submit Experiment</h2>
      <label>Name</label>
      <input value={name} onChange={(e) => setName(e.target.value)} required />
      <label>Description</label>
      <input value={description} onChange={(e) => setDescription(e.target.value)} />
      <label>Provider</label>
      <select value={provider} onChange={(e) => setProvider(e.target.value as Provider)}>
        <option value="local_simulator">Local simulator</option>
        <option value="ibm_runtime">IBM Runtime</option>
      </select>
      <label>Shots</label>
      <input type="number" value={shots} onChange={(e) => setShots(Number(e.target.value))} />
      <label>QASM payload</label>
      <textarea rows={8} value={qasm} onChange={(e) => setQasm(e.target.value)} />
      <button type="submit">Submit job</button>
    </form>
  );
}
