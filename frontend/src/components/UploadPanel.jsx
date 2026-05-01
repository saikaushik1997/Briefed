import { useState, useRef } from 'react'
import axios from 'axios'

export default function UploadPanel({ api, onUpload }) {
  const [dragging, setDragging] = useState(false)
  const [uploads, setUploads] = useState([])
  const inputRef = useRef()

  const updateUpload = (id, patch) =>
    setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, ...patch } : u)))

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.pdf')) return

    const id = crypto.randomUUID()
    setUploads((prev) => [...prev, { id, name: file.name, stage: 'Uploading', cacheHit: false, done: false }])

    const form = new FormData()
    form.append('file', file)

    try {
      const { data } = await axios.post(`${api}/documents/upload`, form)

      if (data.cache_hit) {
        updateUpload(id, { stage: 'Done', cacheHit: true, done: true })
        onUpload()
        return
      }

      const poll = setInterval(async () => {
        const { data: doc } = await axios.get(`${api}/documents/${data.document_id}`)
        const latestStage = doc.stages?.at(-1)?.stage
        if (latestStage) updateUpload(id, { stage: latestStage })

        if (doc.status === 'complete' || doc.status === 'failed') {
          clearInterval(poll)
          updateUpload(id, { stage: doc.status === 'complete' ? 'Done' : 'Failed', done: true })
          onUpload()
        }
      }, 2000)
    } catch {
      updateUpload(id, { stage: 'Error', done: true })
    }
  }

  const clearDone = () => setUploads((prev) => prev.filter((u) => !u.done))

  return (
    <div className="space-y-3">
      <div
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
          ${dragging ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-500'}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
        onClick={() => inputRef.current.click()}
      >
        <input ref={inputRef} type="file" accept=".pdf" className="hidden" onChange={(e) => { handleFile(e.target.files[0]); e.target.value = '' }} />
        <p className="text-slate-400">Drop a PDF here or click to upload</p>
        <p className="text-xs text-slate-600 mt-1">Any document — reports, statements, research papers</p>
      </div>

      {uploads.length > 0 && (
        <div className="space-y-2">
          {uploads.map((u) => (
            <div key={u.id} className="flex items-center justify-between bg-slate-800/40 rounded-lg px-4 py-2 text-sm">
              <span className="text-slate-300 truncate max-w-[40%]">{u.name}</span>
              <div className="flex items-center gap-3">
                {u.cacheHit && <span className="text-green-400 text-xs">cache hit · $0.00</span>}
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  u.stage === 'Done' ? 'bg-green-900/50 text-green-400' :
                  u.stage === 'Failed' || u.stage === 'Error' ? 'bg-red-900/50 text-red-400' :
                  'bg-blue-900/50 text-blue-400'
                }`}>{u.stage}</span>
              </div>
            </div>
          ))}
          {uploads.some((u) => u.done) && (
            <button onClick={clearDone} className="text-xs text-slate-500 hover:text-slate-400">
              Clear completed
            </button>
          )}
        </div>
      )}
    </div>
  )
}
