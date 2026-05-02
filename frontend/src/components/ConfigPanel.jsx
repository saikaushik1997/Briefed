import { useState } from 'react'
import axios from 'axios'

const MODELS = [
  'gpt-4o-mini',
  'gpt-4o',
  'claude-3-5-sonnet-20241022',
  'claude-3-haiku-20240307',
]

export default function ConfigPanel({ api, config, onUpdate }) {
  const [chartModel, setChartModel] = useState('claude-3-5-sonnet-20241022')
  const [synthesisModel, setSynthesisModel] = useState('gpt-4o')
  const [experimentTag, setExperimentTag] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const hasChallenger = !!config?.challenger

  async function handleRegister() {
    setLoading(true)
    setError(null)
    try {
      await axios.post(`${api}/config/challenger`, {
        chart_model: chartModel,
        synthesis_model: synthesisModel,
        experiment_tag: experimentTag,
      })
      onUpdate()
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handlePromote() {
    setLoading(true)
    setError(null)
    try {
      await axios.post(`${api}/config/promote`)
      onUpdate()
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleEnd() {
    setLoading(true)
    setError(null)
    try {
      await axios.delete(`${api}/config/challenger`)
      onUpdate()
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 px-5 py-4 space-y-4">
      <p className="text-sm font-medium text-slate-300">A/B Experiment</p>

      {!hasChallenger ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-slate-400">Chart model</label>
              <select
                value={chartModel}
                onChange={e => setChartModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
              >
                {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-slate-400">Synthesis model</label>
              <select
                value={synthesisModel}
                onChange={e => setSynthesisModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
              >
                {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-slate-400">Experiment tag (optional)</label>
            <input
              type="text"
              value={experimentTag}
              onChange={e => setExperimentTag(e.target.value)}
              placeholder="e.g. chart-model-v2"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600"
            />
          </div>

          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full bg-yellow-600 hover:bg-yellow-500 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            {loading ? 'Registering…' : 'Start Experiment'}
          </button>
        </div>
      ) : (
        <div className="flex gap-3">
          <button
            onClick={handlePromote}
            disabled={loading}
            className="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            {loading ? '…' : 'Promote Challenger'}
          </button>
          <button
            onClick={handleEnd}
            disabled={loading}
            className="flex-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-slate-200 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            {loading ? '…' : 'End Experiment'}
          </button>
        </div>
      )}

      {error && <p className="text-red-400 text-xs">{error}</p>}
    </div>
  )
}
