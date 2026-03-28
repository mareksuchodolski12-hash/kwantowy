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
    return <p className="text-text-muted text-sm">No measurement data available.</p>;
  }

  return (
    <div>
      {title && <h4 className="text-sm font-medium text-text-secondary mb-3">{title}</h4>}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.06)" />
          <XAxis dataKey="state" tick={{ fontSize: 12, fill: '#8888b0' }} stroke="#1c1c4a" />
          <YAxis tick={{ fontSize: 12, fill: '#8888b0' }} stroke="#1c1c4a" />
          <Tooltip
            contentStyle={{
              background: 'rgba(15, 16, 41, 0.95)',
              border: '1px solid rgba(0, 229, 255, 0.15)',
              borderRadius: '8px',
              backdropFilter: 'blur(8px)',
            }}
            labelStyle={{ color: '#00e5ff' }}
            itemStyle={{ color: '#e4e4f7' }}
            formatter={(value, name) => {
              if (name === 'probability') return [`${Number(value).toFixed(1)}%`, 'Probability'];
              return [value, 'Count'];
            }}
          />
          <Bar dataKey="count" fill="url(#barGradient)" radius={[4, 4, 0, 0]} />
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00e5ff" stopOpacity={0.9} />
              <stop offset="100%" stopColor="#a855f7" stopOpacity={0.6} />
            </linearGradient>
          </defs>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
        {data.map((d) => (
          <div key={d.state} className="glass rounded-lg px-3 py-2 text-sm">
            <span className="font-mono font-medium text-accent">{d.state}</span>
            <span className="text-text-secondary ml-2">
              {d.count} ({d.probability.toFixed(1)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
