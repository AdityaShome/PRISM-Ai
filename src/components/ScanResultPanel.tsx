import type { ScanResponse } from './api'

export function ScanResultPanel({ scan }: { scan: ScanResponse }) {
  if (!scan) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        {scan.trust_score !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-3xl font-semibold text-white">{scan.trust_score}</span>
            <span className="text-slate-400">/100</span>
          </div>
        )}
        <div>
          <p className="text-sm font-semibold text-slate-400">{scan.risk_level}</p>
          <p className="text-xs text-slate-500">{scan.confidence}</p>
        </div>
      </div>

      {scan.summary && (
        <p className="text-sm leading-6 text-slate-200">{scan.summary}</p>
      )}

      {scan.recommended_action && (
        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-4">
          <p className="text-xs font-semibold text-cyan-200 mb-2">RECOMMENDATION</p>
          <p className="text-sm text-cyan-50">{scan.recommended_action}</p>
        </div>
      )}
    </div>
  )
}
