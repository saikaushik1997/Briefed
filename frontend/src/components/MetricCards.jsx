export default function MetricCards({ metrics }) {
  const cards = [
    { label: 'Documents', value: metrics.total_documents },
    { label: 'Avg Cost', value: `$${metrics.avg_cost.toFixed(4)}` },
    { label: 'Avg Latency', value: `${metrics.avg_latency.toFixed(1)}s` },
    { label: 'Avg Quality', value: metrics.avg_quality.toFixed(2) },
    { label: 'Cache Hit Rate', value: `${(metrics.cache_hit_rate * 100).toFixed(0)}%` },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
      {cards.map(({ label, value }) => (
        <div key={label} className="bg-slate-800/60 rounded-lg p-4">
          <p className="text-xs text-slate-400">{label}</p>
          <p className="text-xl font-semibold mt-1">{value}</p>
        </div>
      ))}
    </div>
  )
}
