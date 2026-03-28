const PROVIDER_STYLES: Record<string, string> = {
  local_simulator: 'border-accent/30 text-accent bg-accent/10',
  ibm_runtime: 'border-plasma/30 text-plasma bg-plasma/10',
  ionq: 'border-violet-400/30 text-violet-400 bg-violet-400/10',
  rigetti: 'border-nebula/30 text-nebula bg-nebula/10',
  simulator_aer: 'border-teal-400/30 text-teal-400 bg-teal-400/10',
};

const PROVIDER_LABELS: Record<string, string> = {
  local_simulator: 'Local Simulator',
  ibm_runtime: 'IBM Runtime',
  ionq: 'IonQ',
  rigetti: 'Rigetti',
  simulator_aer: 'Aer Simulator',
};

export default function ProviderBadge({ provider }: { provider: string }) {
  const style = PROVIDER_STYLES[provider] ?? 'border-text-muted/30 text-text-secondary bg-text-muted/10';
  const label = PROVIDER_LABELS[provider] ?? provider;
  return (
    <span className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}
