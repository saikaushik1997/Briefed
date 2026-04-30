const STATUS_COLORS = {
  complete: 'text-green-400',
  processing: 'text-yellow-400',
  pending: 'text-slate-400',
  failed: 'text-red-400',
}

export default function DocumentTable({ documents, selectedId, onSelect }) {
  if (!documents.length) {
    return <p className="text-slate-500 text-sm">No documents yet. Upload one above.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-800">
            {['Filename', 'Pages', 'Tables', 'Charts', 'Cost', 'Latency', 'Quality', 'Status'].map((h) => (
              <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr
              key={doc.id}
              onClick={() => onSelect(doc.id === selectedId ? null : doc.id)}
              className={`border-b border-slate-800/50 cursor-pointer hover:bg-slate-800/40 transition-colors
                ${doc.id === selectedId ? 'bg-slate-800/60' : ''}`}
            >
              <td className="py-3 pr-4">
                <span className="font-medium">{doc.filename}</span>
                {doc.cache_hit && <span className="ml-2 text-xs text-green-400">CACHED</span>}
              </td>
              <td className="py-3 pr-4 text-slate-400">{doc.page_count ?? '—'}</td>
              <td className="py-3 pr-4 text-slate-400">{doc.table_count ?? 0}</td>
              <td className="py-3 pr-4 text-slate-400">{doc.chart_count ?? 0}</td>
              <td className="py-3 pr-4 text-slate-400">${doc.total_cost?.toFixed(4) ?? '—'}</td>
              <td className="py-3 pr-4 text-slate-400">{doc.total_latency?.toFixed(1) ?? '—'}s</td>
              <td className="py-3 pr-4 text-slate-400">{doc.quality_score?.toFixed(2) ?? '—'}</td>
              <td className={`py-3 pr-4 font-medium ${STATUS_COLORS[doc.status] ?? 'text-slate-400'}`}>
                {doc.status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
