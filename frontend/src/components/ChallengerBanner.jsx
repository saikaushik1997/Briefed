export default function ChallengerBanner({ config }) {
  if (!config?.challenger) return null

  const { champion, challenger, experiment_active } = config
  const split = Math.round((challenger.traffic_split ?? 0.5) * 100)

  return (
    <div className="rounded-xl border border-yellow-600/40 bg-yellow-900/20 px-5 py-4 text-sm space-y-3">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
        <span className="text-yellow-300 font-medium">A/B Experiment Active</span>
        <span className="ml-auto text-yellow-500 text-xs">50/50 split</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900/50 rounded-lg px-4 py-3 space-y-1">
          <p className="text-slate-400 text-xs uppercase tracking-wide">Champion v{champion.version}</p>
          <p className="text-slate-200">chart: <span className="text-slate-400">{champion.chart_model}</span></p>
          <p className="text-slate-200">synthesis: <span className="text-slate-400">{champion.synthesis_model}</span></p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-4 py-3 space-y-1 border border-yellow-600/20">
          <p className="text-yellow-400 text-xs uppercase tracking-wide">Challenger v{challenger.version}</p>
          <p className="text-slate-200">chart: <span className="text-slate-400">{challenger.chart_model}</span></p>
          <p className="text-slate-200">synthesis: <span className="text-slate-400">{challenger.synthesis_model}</span></p>
        </div>
      </div>

      <p className="text-slate-500 text-xs">
        Promote the challenger to champion via MLflow Model Registry when the experiment concludes.
      </p>
    </div>
  )
}
