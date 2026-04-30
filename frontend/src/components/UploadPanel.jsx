import { useState, useRef } from 'react'
import axios from 'axios'

const STAGES = ['Classifying', 'Extracting text', 'Extracting tables', 'Understanding charts', 'Synthesizing', 'Scoring']

export default function UploadPanel({ api, onUpload }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [stage, setStage] = useState(null)
  const [cacheHit, setCacheHit] = useState(false)
  const inputRef = useRef()

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.pdf')) return
    setUploading(true)
    setCacheHit(false)
    setStage('Uploading')

    const form = new FormData()
    form.append('file', file)

    try {
      const { data } = await axios.post(`${api}/documents/upload`, form)

      if (data.cache_hit) {
        setCacheHit(true)
        setStage('Done (cached)')
        onUpload()
        return
      }

      // Poll for stage updates
      const poll = setInterval(async () => {
        const { data: doc } = await axios.get(`${api}/documents/${data.document_id}`)
        const latestStage = doc.stages?.at(-1)?.stage
        if (latestStage) setStage(latestStage)

        if (doc.status === 'complete' || doc.status === 'failed') {
          clearInterval(poll)
          setStage(doc.status === 'complete' ? 'Done' : 'Failed')
          onUpload()
        }
      }, 2000)
    } catch (e) {
      setStage('Error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
        ${dragging ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-500'}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
      onClick={() => inputRef.current.click()}
    >
      <input ref={inputRef} type="file" accept=".pdf" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />

      {stage ? (
        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-300">{stage}</p>
          {cacheHit && <p className="text-xs text-green-400">Cache hit — returned instantly · $0.00</p>}
          {!cacheHit && stage !== 'Done' && stage !== 'Failed' && (
            <div className="flex justify-center gap-2 mt-3">
              {STAGES.map((s) => (
                <span key={s} className={`text-xs px-2 py-1 rounded-full
                  ${stage === s ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-500'}`}>
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div>
          <p className="text-slate-400">Drop a PDF here or click to upload</p>
          <p className="text-xs text-slate-600 mt-1">Any document — reports, statements, research papers</p>
        </div>
      )}
    </div>
  )
}
