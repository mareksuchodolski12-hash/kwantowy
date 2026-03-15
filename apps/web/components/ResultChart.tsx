'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ResultChartProps {
  counts: Record<string, number>;
  title?: string;
}

export default function ResultChart({ counts, title }: ResultChartProps) {
  const totalShots = Object.values(counts).reduce((a, b) => a + b, 0);

  const data = Object.entries(counts)
    .map(([state, count]) => ({
      state,
      count,
      probability: totalShots > 0 ? (count / totalShots) * 100 : 0,
    }))
    .sort((a, b) => a.state.localeCompare(b.state));

  if (data.length === 0) {
    return <p className="text-gray-500 text-sm">No measurement data available.</p>;
  }

  return (
    <div>
      {title && <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="state" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) => {
              if (name === 'probability') return [`${Number(value).toFixed(1)}%`, 'Probability'];
              return [value, 'Count'];
            }}
          />
          <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
        {data.map((d) => (
          <div key={d.state} className="bg-gray-50 rounded px-3 py-2 text-sm">
            <span className="font-mono font-medium">{d.state}</span>
            <span className="text-gray-500 ml-2">
              {d.count} ({d.probability.toFixed(1)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
