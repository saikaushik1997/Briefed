import { useState, useEffect } from 'react'
import axios from 'axios'

export default function DocumentDetail({ api, documentId, onClose }) {
  const [doc, setDoc] = useState(null)
  const [tab, setTab] = useState('document')

  useEffect(() => {
    const fetch = async () => {
      const { data } = await axios.get(`${api}/documents/${documentId}`)
      setDoc(data)
    }
    fetch()
    const interval = setInterval(fetch, 3000)
    return () => clearInterval(interval)
  }, [documentId])

  if (!doc) return null

  const result = doc.result

  return (
    <div className="bg-slate-800/40 rounded-xl border border-slate-700 p-6 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="font-semibold text-lg">{doc.filename}</h2>
          {doc.cache_hit && <span className="text-xs text-green-400">Cache hit · $0.00 · instant</span>}
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300 text-sm">✕ Close</button>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-4 border-b border-slate-700 text-sm">
        {['document', 'pipeline'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 capitalize transition-colors ${tab === t ? 'text-white border-b-2 border-blue-500' : 'text-slate-400 hover:text-slate-300'}`}
          >
            {t === 'document' ? 'Document' : 'Pipeline & Decisions'}
          </button>
        ))}
      </div>

      {tab === 'document' && result && (
        <div className="space-y-6">
          {/* Plain explanation */}
          <div>
            <p className="text-slate-400 text-xs uppercase tracking-wide mb-2">Summary</p>
            <p className="text-slate-200 leading-relaxed">{result.plain_explanation || '—'}</p>
          </div>

          {/* Key metrics */}
          {result.key_metrics && Object.keys(result.key_metrics).length > 0 && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide mb-2">Key Metrics</p>
              <div className="flex flex-wrap gap-3">
                {Object.entries(result.key_metrics).map(([k, v]) => (
                  <span key={k} className="bg-slate-700 rounded-lg px-3 py-1 text-sm">
                    <span className="text-slate-400">{k}: </span>{v}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tables */}
          {result.structured_json?.tables?.length > 0 && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide mb-2">Tables ({result.structured_json.tables.length})</p>
              <div className="space-y-3">
                {result.structured_json.tables.map((t, i) => (
                  <details key={i} className="bg-slate-900/60 rounded-lg p-4">
                    <summary className="cursor-pointer font-medium">{t.title || `Table ${i + 1}`}</summary>
                    <p className="text-slate-400 text-sm mt-2">{t.interpretation}</p>
                  </details>
                ))}
              </div>
            </div>
          )}

          {/* Charts */}
          {result.structured_json?.charts?.length > 0 && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide mb-2">Charts ({result.structured_json.charts.length})</p>
              <div className="space-y-3">
                {result.structured_json.charts.map((c, i) => (
                  <details key={i} className="bg-slate-900/60 rounded-lg p-4">
                    <summary className="cursor-pointer font-medium">{c.description || `Chart ${i + 1}`}</summary>
                    <p className="text-slate-400 text-sm mt-2">{c.insight}</p>
                  </details>
                ))}
              </div>
            </div>
          )}

          {/* Quality detail */}
          {result.quality_detail && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide mb-2">
                Quality Score: {result.quality_detail.score?.toFixed(2)} · judge: {result.quality_detail.judge_model}
              </p>
              <div className="space-y-1 text-sm">
                {result.quality_detail.faithful_claims?.map((c, i) => (
                  <p key={i} className="text-green-400">✓ {c}</p>
                ))}
                {result.quality_detail.unfaithful_claims?.map((c, i) => (
                  <p key={i} className="text-red-400">✗ {c}</p>
                ))}
                {result.quality_detail.missing_from_explanation?.map((c, i) => (
                  <p key={i} className="text-yellow-400">△ {c}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'pipeline' && (
        <div className="space-y-6">
          {/* Pipeline breakdown */}
          <div>
            <p className="text-slate-400 text-xs uppercase tracking-wide mb-3">Pipeline Breakdown</p>
            <div className="space-y-2">
              {doc.stages?.map((s) => (
                <div key={s.stage} className="flex justify-between items-center text-sm bg-slate-900/40 rounded-lg px-4 py-2">
                  <span className="text-slate-300 capitalize">{s.stage}</span>
                  <span className="text-slate-400 text-xs">{s.model_used || '—'}</span>
                  <span className="text-slate-400">{s.latency?.toFixed(1)}s</span>
                  <span className="text-slate-400">${s.cost?.toFixed(4)}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full
                    ${s.status === 'complete' ? 'bg-green-900/50 text-green-400' :
                      s.status === 'skipped' ? 'bg-slate-700 text-slate-500' :
                      'bg-yellow-900/50 text-yellow-400'}`}>
                    {s.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Decision trace */}
          {doc.decisions?.length > 0 && (
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide mb-3">Decision Trace</p>
              <div className="space-y-2">
                {doc.decisions.map((d, i) => (
                  <div key={i} className="text-sm bg-slate-900/40 rounded-lg px-4 py-3">
                    <div className="flex justify-between">
                      <span className="text-slate-300">{d.stage} · <span className="text-slate-500">{d.decision_type}</span></span>
                      {d.cost_impact !== 0 && (
                        <span className={d.cost_impact < 0 ? 'text-green-400' : 'text-red-400'}>
                          {d.cost_impact < 0 ? `saved $${Math.abs(d.cost_impact).toFixed(4)}` : `+$${d.cost_impact.toFixed(4)}`}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-400 mt-1">→ {d.choice_made}</p>
                    {d.rationale && <p className="text-slate-500 text-xs mt-1">{d.rationale}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
