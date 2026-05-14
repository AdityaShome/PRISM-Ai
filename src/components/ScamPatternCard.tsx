import React from 'react'

export default function ScamPatternCard({ title, risk, example, advice }: { title: string; risk: string; example: string; advice: string }) {
  const color = risk === 'High' ? 'bg-rose-500/10 border-rose-400/15 text-rose-200' : risk === 'Medium' ? 'bg-orange-500/8 border-orange-400/15 text-orange-200' : 'bg-emerald-500/8 border-emerald-400/15 text-emerald-200'
  return (
    <div className={`rounded-[20px] border p-4 ${color}`}>
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        <span className="text-xs text-slate-300">{risk}</span>
      </div>
      <p className="mt-3 text-sm text-slate-300">Example: <span className="text-slate-200">{example}</span></p>
      <p className="mt-2 text-sm text-slate-200">What to do: {advice}</p>
    </div>
  )
}
