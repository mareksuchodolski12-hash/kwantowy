import { listProviders, type ProviderCapabilities } from '@/lib/api';

export const dynamic = 'force-dynamic';

function fidelityColor(f: number): string {
  if (f >= 0.98) return 'text-green-600';
  if (f >= 0.95) return 'text-yellow-600';
  return 'text-red-600';
}

function medal(index: number): string {
  if (index === 0) return '🥇';
  if (index === 1) return '🥈';
  if (index === 2) return '🥉';
  return `#${index + 1}`;
}

export default async function ProvidersPage() {
  let providers: ProviderCapabilities[] = [];
  try {
    providers = await listProviders();
  } catch {
    // API may not be available during build
  }

  const ranked = [...providers].sort((a, b) => b.estimated_fidelity - a.estimated_fidelity);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Quantum Hardware Leaderboard</h2>
        <p className="text-sm text-gray-500 mt-1">
          Provider ranking based on benchmarking data — fidelity, queue time, and cost per shot
        </p>
      </div>

      {ranked.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
          No provider data available. Ensure the API is running and benchmarks have been recorded.
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Fidelity</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Avg Queue Time
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Cost / Shot (USD)
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Max Qubits</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Type</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {ranked.map((p, idx) => (
                <tr key={p.provider} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium">{medal(idx)}</td>
                  <td className="px-4 py-3 text-sm font-semibold text-gray-900">{p.provider}</td>
                  <td className={`px-4 py-3 text-sm text-right font-mono ${fidelityColor(p.estimated_fidelity)}`}>
                    {(p.estimated_fidelity * 100).toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-mono text-gray-700">
                    {p.avg_queue_time_seconds.toFixed(1)}s
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-mono text-gray-700">
                    ${p.estimated_cost_per_shot_usd.toFixed(4)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-mono text-gray-700">{p.max_qubits}</td>
                  <td className="px-4 py-3 text-sm text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${p.is_simulator ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}
                    >
                      {p.is_simulator ? 'Simulator' : 'Hardware'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
