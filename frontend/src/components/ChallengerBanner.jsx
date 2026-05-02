const MODEL_LABELS = {
  classifier_model: 'Classifier',
  text_model: 'Text',
  table_model: 'Table',
  chart_model: 'Chart',
  synthesis_model: 'Synthesis',
  judge_model: 'Judge',
}

export default function ChallengerBanner({ config }) {
  if (!config?.challenger) return null

  const { champion, challenger } = config

  const allKeys = Object.keys(MODEL_LABELS)
  const diffKeys = allKeys.filter(k => champion[k] !== challenger[k])
  const displayKeys = diffKeys.length > 0 ? diffKeys : allKeys

  return (
    <div className="rounded-xl border border-yellow-600/40 bg-yellow-900/20 px-5 py-4 text-sm space-y-3">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
        <span className="text-yellow-300 font-medium">A/B Experiment Active</span>
        <span className="ml-auto text-yellow-500 text-xs">50/50 split</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900/50 rounded-lg px-4 py-3 space-y-1">
          <p className="text-slate-400 text-xs uppercase tracking-wide mb-2">Champion v{champion.version}</p>
          {displayKeys.map(k => (
            <p key={k} className="text-slate-200">
              {MODEL_LABELS[k]}: <span className="text-slate-400">{champion[k]}</span>
            </p>
          ))}
        </div>
        <div className="bg-slate-900/50 rounded-lg px-4 py-3 space-y-1 border border-yellow-600/20">
          <p className="text-yellow-400 text-xs uppercase tracking-wide mb-2">Challenger v{challenger.version}</p>
          {displayKeys.map(k => (
            <p key={k} className="text-slate-200">
              {MODEL_LABELS[k]}: <span className={champion[k] !== challenger[k] ? 'text-yellow-400' : 'text-slate-400'}>
                {challenger[k]}
              </span>
            </p>
          ))}
        </div>
      </div>

      <p className="text-slate-500 text-xs">
        Only changed models shown. Promote the challenger via the panel below when the experiment concludes.
      </p>
    </div>
  )
}
