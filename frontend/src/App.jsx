import { useState, useEffect } from 'react'
import UploadPanel from './components/UploadPanel'
import MetricCards from './components/MetricCards'
import DocumentTable from './components/DocumentTable'
import DocumentDetail from './components/DocumentDetail'
import QualityTrendChart from './components/QualityTrendChart'
import ChallengerBanner from './components/ChallengerBanner'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [documents, setDocuments] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [qualityTrend, setQualityTrend] = useState([])
  const [configStatus, setConfigStatus] = useState(null)
  const [selectedId, setSelectedId] = useState(null)

  const fetchDocuments = async () => {
    const { data } = await axios.get(`${API}/documents`)
    setDocuments(data)
  }

  const fetchMetrics = async () => {
    const { data } = await axios.get(`${API}/metrics/summary`)
    setMetrics(data)
  }

  const fetchQualityTrend = async () => {
    const { data } = await axios.get(`${API}/metrics/quality-trend`)
    setQualityTrend(data)
  }

  const fetchConfigStatus = async () => {
    const { data } = await axios.get(`${API}/config/status`)
    setConfigStatus(data)
  }

  useEffect(() => {
    fetchDocuments()
    fetchMetrics()
    fetchQualityTrend()
    fetchConfigStatus()
    const interval = setInterval(() => {
      fetchDocuments()
      fetchMetrics()
      fetchQualityTrend()
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Briefed</h1>
        <p className="text-slate-400 text-sm mt-1">Upload any document. Get the point.</p>
      </header>

      {configStatus && <ChallengerBanner config={configStatus} />}

      <UploadPanel api={API} onUpload={fetchDocuments} />

      {metrics && <MetricCards metrics={metrics} />}

      {qualityTrend.length > 1 && <QualityTrendChart data={qualityTrend} />}

      <DocumentTable
        documents={documents}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />

      {selectedId && (
        <DocumentDetail
          api={API}
          documentId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}
