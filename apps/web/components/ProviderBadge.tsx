const PROVIDER_STYLES: Record<string, string> = {
  local_simulator: 'bg-blue-100 text-blue-800',
  ibm_runtime: 'bg-indigo-100 text-indigo-800',
  ionq: 'bg-purple-100 text-purple-800',
  rigetti: 'bg-pink-100 text-pink-800',
  simulator_aer: 'bg-cyan-100 text-cyan-800',
};

const PROVIDER_LABELS: Record<string, string> = {
  local_simulator: 'Local Simulator',
  ibm_runtime: 'IBM Runtime',
  ionq: 'IonQ',
  rigetti: 'Rigetti',
  simulator_aer: 'Aer Simulator',
};

export default function ProviderBadge({ provider }: { provider: string }) {
  const style = PROVIDER_STYLES[provider] ?? 'bg-gray-100 text-gray-700';
  const label = PROVIDER_LABELS[provider] ?? provider;
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}
