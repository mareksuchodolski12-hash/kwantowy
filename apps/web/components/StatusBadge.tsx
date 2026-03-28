const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  queued: { bg: 'bg-text-muted/10', text: 'text-text-secondary', dot: 'bg-text-secondary' },
  submitted: { bg: 'bg-text-muted/10', text: 'text-text-secondary', dot: 'bg-text-secondary' },
  running: { bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-400 animate-pulse' },
  succeeded: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', dot: 'bg-emerald-400' },
  failed: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-400' },
};

export default function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.queued;
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${s.bg} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {label}
    </span>
  );
}
