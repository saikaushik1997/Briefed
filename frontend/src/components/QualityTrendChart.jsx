import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs space-y-1">
      <p className="text-slate-300 font-medium truncate max-w-[180px]">{d.filename}</p>
      <p className="text-white">Score: <span className="text-blue-400">{d.quality_score}</span></p>
      <p className="text-slate-400">Cost: ${d.total_cost}</p>
      <p className="text-slate-500">Config: v{d.config_bundle_version}</p>
    </div>
  )
}

export default function QualityTrendChart({ data }) {
  if (!data?.length) return null

  const chartData = data.map((d, i) => ({ ...d, index: i + 1 }))
  const avg = data.reduce((s, d) => s + d.quality_score, 0) / data.length

  return (
    <div className="bg-slate-800/40 rounded-xl border border-slate-700 p-5">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm font-medium text-slate-300">Quality Trend</p>
        <span className="text-xs text-slate-500">avg {avg.toFixed(2)} · {data.length} docs</span>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="index" tick={{ fontSize: 11, fill: '#64748b' }} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: '#64748b' }} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={avg} stroke="#64748b" strokeDasharray="4 4" />
          <Line
            type="monotone"
            dataKey="quality_score"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3, fill: '#3b82f6' }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
