import { getComparison } from '@/lib/api';

export default async function ComparisonPage() {
  const comparison = await getComparison();
  const rows = Object.entries(comparison);

  return (
    <section>
      <h2>Local vs Remote Comparison</h2>
      <p>Provider-level summary from control-plane comparison endpoint.</p>
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Runs</th>
            <th>Average duration (ms)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([provider, stats]) => (
            <tr key={provider}>
              <td>{provider}</td>
              <td>{stats.runs}</td>
              <td>{Math.round(stats.avg_duration_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
