import React, { useEffect, useState } from 'react'
import { getScans, type ScanResponse } from '../lib/api'

export default function ScanHistory() {
  const [items, setItems] = useState<Array<Partial<ScanResponse> & { scan_id: string }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    getScans()
      .then((data) => {
        if (!mounted) return
        setItems(data)
      })
      .catch((err) => setError(err.message || 'Failed to load scans'))
      .finally(() => setLoading(false))

    return () => {
      mounted = false
    }
  }, [])

  if (loading) return <div className="py-8 text-center text-slate-400">Loading history...</div>
  if (error) return <div className="py-8 text-center text-rose-200">{error}</div>
  if (items.length === 0) return <div className="py-8 text-center text-slate-400">No scans yet.</div>

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full table-auto text-sm">
        <thead>
          <tr className="text-left text-slate-400">
            <th className="px-3 py-2">Date</th>
            <th className="px-3 py-2">Company / Title</th>
            <th className="px-3 py-2">Trust</th>
            <th className="px-3 py-2">Risk</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody className="mt-2 divide-y divide-white/6">
          {items.map((it) => (
            <tr key={it.scan_id} className="border-t border-white/4">
              <td className="px-3 py-3 text-slate-300">{new Date(it.created_at ?? Date.now()).toLocaleString()}</td>
              <td className="px-3 py-3 text-slate-200">{(it.extracted_details && (it.extracted_details as any).company) || it.summary || it.scan_id}</td>
              <td className="px-3 py-3 text-slate-200">{it.trust_score ?? '—'}</td>
              <td className="px-3 py-3 text-slate-200">{it.risk_level ?? '—'}</td>
              <td className="px-3 py-3 text-slate-200">{it.workflow_status ?? '—'}</td>
              <td className="px-3 py-3">
                <div className="flex gap-2">
                  <a className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200" href={`#/scans/${it.scan_id}`}>
                    View
                  </a>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
