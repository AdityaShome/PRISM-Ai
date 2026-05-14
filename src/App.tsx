import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode, RefObject } from 'react'
import {
  AlertTriangle,
  BadgeCheck,
  Brain,
  CheckCircle,
  Clock,
  Loader,
  Map,
  Radar,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  XCircle,
} from 'lucide-react'
import {
  categoryChips,
  categoryPresets,
  growthTrend,
  listings,
  modeFilters,
  recommendationSummary,
  riskDistribution,
  riskFilters,
  roleFilters,
  stipendFilters,
  useCaseCards,
} from './data/mock'
import { API_BASE_CANDIDATES, startScan, submitReview, type ScanResponse } from './lib/api'
import ScanHistory from './components/ScanHistory'
import ScamPatternCard from './components/ScamPatternCard'

type ModalMode = 'cover' | 'checklist' | null

type Tone = {
  label: string
  className: string
  icon: typeof CheckCircle
}

const navItems = [
  { label: 'Home', target: 'home' },
  { label: 'Scan', target: 'discover' },
  { label: 'Results', target: 'verify' },
  { label: 'History', target: 'history' },
  { label: 'Learn', target: 'learn' },
  { label: 'Insights', target: 'insights' },
  { label: 'Recommendations', target: 'recommendations' },
]

const densityMap = [
  [1, 2, 2, 3, 2, 1],
  [2, 3, 4, 5, 3, 2],
  [1, 2, 4, 5, 4, 2],
  [1, 2, 3, 4, 3, 2],
]

const compareReasons = [
  'Highest trust score among paid internships',
  'Clear role and responsibilities',
  'Verified recruiter profile',
  'Strong match for students with project experience',
  'Low scam risk',
  'Good growth signal in backend/API roles',
]
const liveTraceSteps = [
  { text: 'Discovering internship posts...', status: 'completed' },
  { text: 'Checking company identity...', status: 'verified' },
  { text: 'Comparing similar listings...', status: 'completed' },
  { text: 'Detecting payment-risk language...', status: 'warning' },
  { text: 'Analyzing review patterns...', status: 'warning' },
  { text: 'Ranking by trust and growth...', status: 'verified' },
  { text: 'Recommendation ready.', status: 'completed' },
] as const

const formatCategoryPlaceholder = (category: string) => {
  switch (category) {
    case 'PGs':
      return 'Search PGs, hostels, rooms, rentals...'
    case 'Scholarships':
      return 'Search scholarships, fellowships, grants...'
    case 'Hackathons':
      return 'Search hackathons, events, builder jams...'
    case 'Used Laptops':
      return 'Search used laptops, refurbished deals...'
    case 'Courses':
      return 'Search courses, bootcamps, certifications...'
    case 'Food Places':
      return 'Search food places, cafes, student spots...'
    case 'Local Services':
      return 'Search local services, repairs, tutors...'
    default:
      return 'Search internships, scholarships, PGs, courses, hackathons...'
  }
}

const trustTone = (score: number): Tone => {
  if (score >= 80) {
    return {
      label: 'Trusted',
      className: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
      icon: CheckCircle,
    }
  }

  if (score >= 60) {
    return {
      label: 'Caution',
      className: 'border-orange-400/30 bg-orange-500/10 text-orange-300',
      icon: AlertTriangle,
    }
  }

  return {
    label: 'Risky',
    className: 'border-rose-400/30 bg-rose-500/10 text-rose-300',
    icon: XCircle,
  }
}

const riskTone = (risk: string): Tone => {
  if (risk === 'Low') {
    return {
      label: 'Low risk',
      className: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
      icon: ShieldCheck,
    }
  }

  if (risk === 'Medium') {
    return {
      label: 'Medium risk',
      className: 'border-orange-400/30 bg-orange-500/10 text-orange-300',
      icon: AlertTriangle,
    }
  }

  return {
    label: 'High risk',
    className: 'border-rose-400/30 bg-rose-500/10 text-rose-300',
    icon: XCircle,
  }
}

function SectionHeading({
  eyebrow,
  title,
  subtitle,
  right,
}: {
  eyebrow: string
  title: string
  subtitle: string
  right?: ReactNode
}) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="max-w-3xl space-y-2">
        <p className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">
          <Sparkles className="h-3.5 w-3.5" />
          {eyebrow}
        </p>
        <h2 className="text-3xl font-semibold tracking-tight text-white md:text-4xl">{title}</h2>
        <p className="text-sm leading-6 text-slate-300 md:text-base">{subtitle}</p>
      </div>
      {right ? <div>{right}</div> : null}
    </div>
  )
}

function ScoreRing({ score, size = 152 }: { score: number; size?: number }) {
  const stroke = 11
  const radius = (size - stroke) / 2 - 4
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const tone = trustTone(score)
  const Icon = tone.icon

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="score-gradient" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(148,163,184,0.18)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#score-gradient)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <Icon className="mb-2 h-5 w-5 text-cyan-200/90" />
        <p className="text-3xl font-semibold text-white">{score}</p>
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-300">/ 100</p>
      </div>
      <div className="absolute -bottom-2 rounded-full border border-white/10 bg-slate-950/80 px-3 py-1 text-xs font-semibold text-white shadow-lg">
        {tone.label}
      </div>
    </div>
  )
}

function DensityGrid() {
  return (
    <div className="grid grid-cols-6 gap-2 rounded-3xl border border-white/10 bg-slate-950/40 p-4">
      {densityMap.flatMap((row, rowIndex) =>
        row.map((value, columnIndex) => {
          const intensity = value / 5
          return (
            <div
              key={`${rowIndex}-${columnIndex}`}
              className="flex items-center justify-center"
              style={{ minHeight: 26 }}
            >
              <span
                className="block rounded-full"
                style={{
                  width: 10 + intensity * 12,
                  height: 10 + intensity * 12,
                  background:
                    value >= 5
                      ? 'radial-gradient(circle, rgba(34,211,238,1), rgba(139,92,246,0.95))'
                      : value >= 4
                        ? 'radial-gradient(circle, rgba(34,211,238,0.92), rgba(34,211,238,0.35))'
                        : value >= 3
                          ? 'radial-gradient(circle, rgba(96,165,250,0.82), rgba(96,165,250,0.22))'
                          : 'radial-gradient(circle, rgba(148,163,184,0.55), rgba(148,163,184,0.1))',
                  boxShadow:
                    value >= 4
                      ? '0 0 0 6px rgba(34,211,238,0.08), 0 0 22px rgba(34,211,238,0.28)'
                      : '0 0 0 4px rgba(148,163,184,0.06)',
                }}
              />
            </div>
          )
        }),
      )}
    </div>
  )
}

function LineChart({ width = 520, height = 240 }: { width?: number; height?: number }) {
  const paddingX = 44
  const paddingY = 28
  const max = Math.max(...Object.values(growthTrend.series).flat())
  const min = 0
  const chartWidth = width - paddingX * 2
  const chartHeight = height - paddingY * 2

  const series = [
    { name: 'Frontend', values: growthTrend.series.Frontend, color: '#22d3ee' },
    { name: 'AI/ML', values: growthTrend.series['AI/ML'], color: '#a78bfa' },
    { name: 'Backend', values: growthTrend.series.Backend, color: '#34d399' },
  ]

  const buildPoints = (values: number[]) =>
    values
      .map((value, index) => {
        const x = paddingX + (index * chartWidth) / (values.length - 1)
        const y = paddingY + chartHeight - ((value - min) / (max - min || 1)) * chartHeight
        return `${x},${y}`
      })
      .join(' ')

  return (
    <div className="overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/45 p-5 shadow-[0_24px_60px_rgba(2,6,23,0.32)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Growth Trend</h3>
          <p className="text-sm text-slate-400">AI/ML internships up 32% this month.</p>
        </div>
        <div className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
          Growth signal
        </div>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full">
        <defs>
          <linearGradient id="chart-grid" x1="0%" x2="0%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(148,163,184,0.24)" />
            <stop offset="100%" stopColor="rgba(148,163,184,0.04)" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((line) => {
          const y = paddingY + chartHeight * line
          return <line key={line} x1={paddingX} x2={width - paddingX} y1={y} y2={y} stroke="rgba(148,163,184,0.18)" />
        })}
        {series.map((item) => (
          <g key={item.name}>
            <polyline
              points={buildPoints(item.values)}
              fill="none"
              stroke={item.color}
              strokeWidth="3"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {item.values.map((value, index) => {
              const x = paddingX + (index * chartWidth) / (item.values.length - 1)
              const y = paddingY + chartHeight - ((value - min) / (max - min || 1)) * chartHeight
              return <circle key={`${item.name}-${index}`} cx={x} cy={y} r="4.5" fill={item.color} />
            })}
          </g>
        ))}
        {growthTrend.labels.map((label, index) => {
          const x = paddingX + (index * chartWidth) / (growthTrend.labels.length - 1)
          return (
            <text key={label} x={x} y={height - 8} fill="rgba(226,232,240,0.68)" fontSize="11" textAnchor="middle">
              {label}
            </text>
          )
        })}
      </svg>
      <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-300">
        {series.map((item) => (
          <div key={item.name} className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
            {item.name}
          </div>
        ))}
      </div>
    </div>
  )
}

function RiskDistributionCard() {
  return (
    <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5 shadow-[0_24px_60px_rgba(2,6,23,0.32)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Risk Distribution</h3>
          <p className="text-sm text-slate-400">How the demo catalog breaks down by trust level.</p>
        </div>
        <ShieldCheck className="h-5 w-5 text-emerald-300" />
      </div>
      <div className="space-y-4">
        {riskDistribution.map((item) => {
          const color =
            item.label === 'Low Risk' ? '#34d399' : item.label === 'Medium Risk' ? '#fb923c' : '#fb7185'
          return (
            <div key={item.label} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-200">{item.label}</span>
                <span className="text-slate-400">{item.value}%</span>
              </div>
              <div className="h-3 rounded-full bg-white/[0.06]">
                <div className="h-full rounded-full" style={{ width: `${item.value}%`, backgroundColor: color }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function TraceStatusBadge({ status }: { status: (typeof liveTraceSteps)[number]['status'] }) {
  const badgeClass =
    status === 'completed'
      ? 'border-emerald-400/20 bg-emerald-500/10 text-emerald-100'
      : status === 'verified'
        ? 'border-cyan-400/20 bg-cyan-500/10 text-cyan-100'
        : 'border-orange-400/20 bg-orange-500/10 text-orange-100'

  const iconClass = status === 'warning' ? 'text-orange-300' : status === 'verified' ? 'text-cyan-200' : 'text-emerald-200'

  const label = status === 'verified' ? 'verified' : status === 'warning' ? 'warning' : 'completed'
  const icon = status === 'warning' ? AlertTriangle : status === 'verified' ? BadgeCheck : CheckCircle
  const Icon = icon

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${badgeClass}`}>
      <Icon className={`h-3.5 w-3.5 ${iconClass}`} />
      {label}
    </span>
  )
}

function LiveAgentTracePanel() {
  return (
    <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Live Agent Trace</p>
          <h3 className="mt-1 text-lg font-semibold text-white">How Prism reached the recommendation</h3>
        </div>
        <div className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
          Trace live
        </div>
      </div>

      <div className="space-y-3">
        {liveTraceSteps.map((step, index) => (
          <div key={step.text} className="flex items-start gap-3 rounded-2xl border border-white/8 bg-white/[0.03] p-3.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-slate-900/80 text-xs font-semibold text-slate-100">
              {index + 1}
            </div>
            <div className="min-w-0 flex-1 space-y-1">
              <p className="text-sm font-medium text-slate-100">{step.text}</p>
              <div className="flex items-center gap-2">
                <TraceStatusBadge status={step.status} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ListingCard({
  listing,
  selected,
  saved,
  onSelect,
  onSave,
}: {
  listing: (typeof listings)[number]
  selected: boolean
  saved: boolean
  onSelect: () => void
  onSave: () => void
}) {
  const trust = trustTone(listing.trustScore)
  const risk = riskTone(listing.risk)
  const TrustIcon = trust.icon
  const RiskIcon = risk.icon

  return (
    <article
      className={`group relative overflow-hidden rounded-[28px] border p-5 transition duration-300 hover:-translate-y-1 hover:border-cyan-300/30 hover:shadow-[0_20px_60px_rgba(34,211,238,0.12)] ${
        selected ? 'border-cyan-300/40 bg-white/[0.07]' : 'border-white/10 bg-slate-950/40'
      }`}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.12),transparent_36%),radial-gradient(circle_at_bottom_left,rgba(139,92,246,0.1),transparent_40%)] opacity-0 transition duration-300 group-hover:opacity-100" />
      <div className="relative flex h-full flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-lg font-semibold text-white">{listing.title}</p>
              {listing.trustScore >= 80 ? <BadgeCheck className="h-4.5 w-4.5 text-emerald-300" /> : null}
            </div>
            <p className="text-sm text-slate-400">{listing.company}</p>
          </div>
          <div className={`rounded-2xl border px-3 py-2 text-center ${trust.className}`}>
            <div className="text-[10px] font-semibold uppercase tracking-[0.24em]">Trust</div>
            <div className="text-xl font-semibold">{listing.trustScore}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 text-xs font-medium">
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 ${risk.className}`}>
            <RiskIcon className="h-3.5 w-3.5" />
            {risk.label}
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-slate-200">{listing.stipend}</span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-slate-200">{listing.mode}</span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-slate-200">{listing.duration}</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {listing.tags.map((tag) => (
            <span key={tag} className="rounded-full border border-cyan-400/15 bg-cyan-500/[0.08] px-3 py-1.5 text-xs text-cyan-100">
              {tag}
            </span>
          ))}
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
            <Brain className="h-3.5 w-3.5 text-violet-300" />
            AI verdict
          </div>
          <p className="text-sm leading-6 text-slate-200">{listing.verdict}</p>
        </div>

        <div className="mt-auto flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onSelect}
            className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-100 transition hover:border-cyan-300/30 hover:bg-cyan-500/15"
          >
            <ShieldCheck className="h-4 w-4" />
            View Trust Check
          </button>
          <button
            type="button"
            onClick={onSave}
            className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition ${
              saved
                ? 'border-emerald-400/25 bg-emerald-500/15 text-emerald-200'
                : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'
            }`}
          >
            {saved ? <CheckCircle className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            {saved ? 'Saved' : 'Save'}
          </button>
        </div>
      </div>
    </article>
  )
}

function CategoryCard({
  title,
  subtitle,
  description,
  selected,
  onClick,
}: {
  title: string
  subtitle: string
  description: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group text-left rounded-[28px] border p-5 transition duration-300 hover:-translate-y-1 ${
        selected
          ? 'border-cyan-300/40 bg-[linear-gradient(180deg,rgba(34,211,238,0.12),rgba(139,92,246,0.08))] shadow-[0_20px_60px_rgba(34,211,238,0.12)]'
          : 'border-white/10 bg-slate-950/40 hover:border-white/20'
      }`}
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-base font-semibold text-white">{title}</p>
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-cyan-200/80">{subtitle}</p>
        </div>
        {selected ? <BadgeCheck className="h-5 w-5 text-emerald-300" /> : <Radar className="h-5 w-5 text-slate-500 transition group-hover:text-cyan-200" />}
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">{description}</p>
    </button>
  )
}

function ActionTile({
  title,
  description,
  icon: Icon,
  buttonLabel,
  onClick,
  accent = 'cyan',
}: {
  title: string
  description: string
  icon: typeof Sparkles
  buttonLabel: string
  onClick: () => void
  accent?: 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose'
}) {
  const accents = {
    cyan: 'border-cyan-400/20 bg-cyan-500/10 text-cyan-100',
    violet: 'border-violet-400/20 bg-violet-500/10 text-violet-100',
    emerald: 'border-emerald-400/20 bg-emerald-500/10 text-emerald-100',
    amber: 'border-orange-400/20 bg-orange-500/10 text-orange-100',
    rose: 'border-rose-400/20 bg-rose-500/10 text-rose-100',
  }[accent]

  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex h-full flex-col justify-between rounded-[28px] border border-white/10 bg-slate-950/40 p-5 text-left transition hover:-translate-y-1 hover:border-white/20 hover:bg-slate-950/55"
    >
      <div>
        <div className={`inline-flex rounded-2xl border p-3 ${accents}`}>
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="mt-4 text-lg font-semibold text-white">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-300">{description}</p>
      </div>
      <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-cyan-100 transition group-hover:translate-x-1">
        <Send className="h-4 w-4" />
        {buttonLabel}
      </div>
    </button>
  )
}

function PrismHeroVisual() {
  return (
    <div className="glass-card relative overflow-hidden rounded-[34px] p-6 shadow-[0_30px_100px_rgba(2,6,23,0.45)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_25%,rgba(34,211,238,0.18),transparent_30%),radial-gradient(circle_at_70%_20%,rgba(139,92,246,0.18),transparent_26%),radial-gradient(circle_at_center,rgba(16,185,129,0.08),transparent_46%)]" />
      <div className="absolute left-1/2 top-1/2 h-[390px] w-[390px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/20" />
      <div className="absolute left-1/2 top-1/2 h-[290px] w-[290px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/15" />
      <div className="absolute left-1/2 top-1/2 h-[200px] w-[200px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/12" />
      <div className="absolute left-1/2 top-1/2 h-[100px] w-[100px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/12 bg-white/[0.02] shadow-[0_0_80px_rgba(34,211,238,0.18)]" />

      <div className="relative flex flex-col items-center gap-4 py-10 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-100">
          <Radar className="h-3.5 w-3.5" />
          Trust radar live
        </div>
        <div className="flex items-center justify-center gap-4">
          <ScoreRing score={86} size={168} />
          <div className="grid gap-3 text-left sm:grid-cols-2">
            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-200">Risk level</p>
              <p className="mt-1 text-xl font-semibold text-white">Low</p>
            </div>
            <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cyan-200">Verified sources</p>
              <p className="mt-1 text-xl font-semibold text-white">12</p>
            </div>
            <div className="rounded-2xl border border-orange-400/20 bg-orange-500/10 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-orange-200">Suspicious signals</p>
              <p className="mt-1 text-xl font-semibold text-white">3</p>
            </div>
            <div className="rounded-2xl border border-violet-400/20 bg-violet-500/10 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-violet-200">Growth trend</p>
              <p className="mt-1 text-xl font-semibold text-white">+32%</p>
            </div>
          </div>
        </div>

        <div className="mt-1 flex flex-wrap justify-center gap-2">
          {['Internships', 'PGs', 'Scholarships', 'Hackathons', 'Used Laptops', 'Courses'].map((chip, index) => (
            <span
              key={chip}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium ${
                index === 0
                  ? 'border-cyan-300/30 bg-cyan-500/10 text-cyan-100'
                  : 'border-white/10 bg-white/5 text-slate-300'
              }`}
            >
              {chip}
            </span>
          ))}
        </div>
      </div>

      <div className="pointer-events-none absolute left-8 top-8 h-3 w-3 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(34,211,238,0.85)] animate-pulseSoft" />
      <div className="pointer-events-none absolute bottom-12 right-10 h-4 w-4 rounded-full bg-violet-300 shadow-[0_0_18px_rgba(167,139,250,0.85)] animate-float" />
      <div className="pointer-events-none absolute bottom-20 left-10 h-2.5 w-2.5 rounded-full bg-emerald-300 shadow-[0_0_18px_rgba(52,211,153,0.85)] animate-float" />
    </div>
  )
}

function Modal({
  mode,
  title,
  listingTitle,
  listingCompany,
  onClose,
}: {
  mode: ModalMode
  title: string
  listingTitle: string
  listingCompany: string
  onClose: () => void
}) {
  if (!mode) {
    return null
  }

  const coverMessage = `Hi, I’m interested in the ${listingTitle} role at ${listingCompany}. Could you please confirm the official application process, stipend details, expected responsibilities, and whether there are any fees involved? Thank you.`
  const checklistItems = [
    'Use the official application link only',
    'Confirm stipend and duration in writing',
    'Verify recruiter identity before sharing documents',
    'Check for fees, WhatsApp-only contact, or urgency traps',
    'Save the deadline and follow up through official channels',
  ]

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/75 px-4 py-8 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-[30px] border border-white/10 bg-slate-950/95 p-6 shadow-[0_30px_120px_rgba(2,6,23,0.7)]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-100">
              <ShieldCheck className="h-3.5 w-3.5" />
              Safe action helper
            </p>
            <h3 className="mt-4 text-2xl font-semibold text-white">{title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-200 transition hover:bg-white/10"
          >
            <XCircle className="h-5 w-5" />
          </button>
        </div>

        {mode === 'cover' ? (
          <div className="mt-6 rounded-[24px] border border-white/10 bg-slate-900/70 p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Generated message</p>
            <p className="text-base leading-8 text-slate-100">“{coverMessage}”</p>
          </div>
        ) : (
          <div className="mt-6 rounded-[24px] border border-white/10 bg-slate-900/70 p-5">
            <p className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Application checklist</p>
            <div className="space-y-3">
              {checklistItems.map((item) => (
                <div key={item} className="flex items-start gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-3 text-sm text-slate-200">
                  <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-500/15"
          >
            Close preview
          </button>
        </div>
      </div>
    </div>
  )
}

function Toast({ message }: { message: string | null }) {
  if (!message) {
    return null
  }

  return (
    <div className="fixed bottom-6 left-1/2 z-[90] -translate-x-1/2">
      <div className="rounded-full border border-emerald-400/20 bg-slate-950/90 px-4 py-3 text-sm font-medium text-slate-100 shadow-[0_18px_50px_rgba(2,6,23,0.65)] backdrop-blur">
        {message}
      </div>
    </div>
  )
}

export default function App() {
  const [selectedCategory, setSelectedCategory] = useState('Internships')
  const [activeRole, setActiveRole] = useState(roleFilters[0])
  const [activeMode, setActiveMode] = useState(modeFilters[0])
  const [activeStipend, setActiveStipend] = useState(stipendFilters[0])
  const [activeRisk, setActiveRisk] = useState(riskFilters[0])
  const [activeGrowth, setActiveGrowth] = useState('High growth roles')
  
  // Real scan state
  const [currentScan, setCurrentScan] = useState<ScanResponse | null>(null)
  const [scanInputText, setScanInputText] = useState('')
  const [scanInputUrl, setScanInputUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  
  // Demo state
  const [selectedListingId, setSelectedListingId] = useState(listings[0].id)
  const [savedListingIds, setSavedListingIds] = useState<number[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [modalMode, setModalMode] = useState<ModalMode>(null)
  const discoveryRef = useRef<HTMLElement | null>(null)
  const verifyRef = useRef<HTMLElement | null>(null)
  const insightsRef = useRef<HTMLElement | null>(null)
  const recommendationsRef = useRef<HTMLElement | null>(null)
  const historyRef = useRef<HTMLElement | null>(null)
  const learnRef = useRef<HTMLElement | null>(null)

  const selectedListing = useMemo(
    () => listings.find((listing) => listing.id === selectedListingId) ?? listings[0],
    [selectedListingId],
  )

  const handleScanSubmit = async () => {
    if (!scanInputText && !scanInputUrl) {
      setError('Please enter internship text or a URL')
      return
    }

    setIsLoading(true)
    setError(null)
    try {
      const result = await startScan(scanInputText || null, scanInputUrl || null, 'internship')
      setCurrentScan(result)
      setToastMessage('Scan submitted to Prism AI')
      scrollToSection(verifyRef)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Scan failed'
      setError(message)
      setToastMessage(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReviewDecision = async (decision: string) => {
    if (!currentScan) return

    setIsLoading(true)
    setError(null)
    try {
      const result = await submitReview(currentScan.scan_id, decision, reviewNotes || null)
      setCurrentScan(result)
      setReviewNotes('')
      setToastMessage(`Review submitted: ${decision}`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Review submission failed'
      setError(message)
      setToastMessage(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!toastMessage) {
      return undefined
    }

    const timeout = window.setTimeout(() => setToastMessage(null), 2800)
    return () => window.clearTimeout(timeout)
  }, [toastMessage])

  const scrollToSection = (section: RefObject<HTMLElement | null>) => {
    section.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const setToast = (message: string) => {
    setToastMessage(message)
  }

  const toggleSave = (listingId: number) => {
    setSavedListingIds((current) =>
      current.includes(listingId) ? current.filter((value) => value !== listingId) : [...current, listingId],
    )
  }

  const isSaved = (listingId: number) => savedListingIds.includes(listingId)
  const trust = trustTone(selectedListing.trustScore)
  const risk = riskTone(selectedListing.risk)
  const placeholder = formatCategoryPlaceholder(selectedCategory)
  const lens = `${activeRole} • ${activeMode} • ${activeStipend} • ${activeRisk} • ${activeGrowth}`

  return (
    <div className="relative isolate min-h-screen overflow-hidden px-4 pb-12 pt-4 sm:px-6 lg:px-8">
      <div className="absolute inset-x-0 top-0 -z-10 h-[700px] bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.16),transparent_30%),radial-gradient(circle_at_20%_10%,rgba(139,92,246,0.18),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(16,185,129,0.08),transparent_24%)]" />
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8">
        <header className="sticky top-4 z-50">
          <div className="glass-card flex flex-wrap items-center justify-between gap-4 rounded-[28px] px-4 py-3 sm:px-6">
            <button
              type="button"
              onClick={() => scrollToSection(discoveryRef)}
              className="flex items-center gap-3 text-left"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#8b5cf6,#06b6d4)] shadow-[0_18px_40px_rgba(34,211,238,0.24)]">
                <Radar className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-lg font-semibold text-white">Prism AI</p>
                <p className="text-xs text-slate-400">See what&apos;s real. Avoid what&apos;s risky.</p>
              </div>
            </button>

            <nav className="flex flex-wrap items-center gap-2 text-sm text-slate-300">
              {navItems.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => {
                    if (item.target === 'discover') scrollToSection(discoveryRef)
                    if (item.target === 'verify') scrollToSection(verifyRef)
                    if (item.target === 'insights') scrollToSection(insightsRef)
                    if (item.target === 'recommendations') scrollToSection(recommendationsRef)
                    if (item.target === 'history') scrollToSection(historyRef)
                    if (item.target === 'learn') scrollToSection(learnRef)
                  }}
                  className="rounded-full px-4 py-2 transition hover:bg-white/[0.08] hover:text-white"
                >
                  {item.label}
                </button>
              ))}
            </nav>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 lg:inline-flex">
                API: {API_BASE_CANDIDATES[0] || 'unknown'}
              </div>
              <div className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-200 md:inline-flex">
                <ShieldCheck className="h-3.5 w-3.5" />
                AI Trust Radar Active
              </div>
              <button
                type="button"
                onClick={() => scrollToSection(discoveryRef)}
                className="rounded-full bg-[linear-gradient(135deg,#8b5cf6,#06b6d4)] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(139,92,246,0.25)] transition hover:scale-[1.02]"
              >
                Scan Now
              </button>
            </div>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="section-shell p-7 sm:p-9 lg:p-10">
            <div className="relative z-10 max-w-2xl space-y-6">
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full border border-violet-400/20 bg-violet-500/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.24em] text-violet-100">
                  AI-powered trust radar
                </span>
                <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-100">
                  Internship Scam Detection demo
                </span>
              </div>

              <div className="space-y-4">
                <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
                  Find what&apos;s real. Avoid what&apos;s risky.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                  Prism AI scans listings, opportunities, reviews, and market signals to detect risk and recommend the safest best option.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => scrollToSection(discoveryRef)}
                  className="rounded-full bg-[linear-gradient(135deg,#8b5cf6,#06b6d4)] px-6 py-3 text-sm font-semibold text-white shadow-[0_18px_50px_rgba(34,211,238,0.2)] transition hover:scale-[1.02]"
                >
                  Start Trust Scan
                </button>
                <button
                  type="button"
                  onClick={() => scrollToSection(selectedListing ? verifyRef : discoveryRef)}
                  className="rounded-full border border-white/10 bg-white/[0.06] px-6 py-3 text-sm font-semibold text-slate-100 transition hover:border-white/20 hover:bg-white/10"
                >
                  View Demo
                </button>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  { label: 'Verified signals', value: '12', icon: BadgeCheck },
                  { label: 'Risk patterns', value: '3', icon: AlertTriangle },
                  { label: 'Growth lift', value: '+32%', icon: TrendingUp },
                ].map((metric) => {
                  const MetricIcon = metric.icon
                  return (
                    <div key={metric.label} className="rounded-[24px] border border-white/10 bg-slate-950/40 p-4">
                      <div className="flex items-center justify-between text-slate-300">
                        <span className="text-xs font-semibold uppercase tracking-[0.2em]">{metric.label}</span>
                        <MetricIcon className="h-4 w-4 text-cyan-200" />
                      </div>
                      <p className="mt-3 text-2xl font-semibold text-white">{metric.value}</p>
                      <p className="mt-1 text-xs text-slate-400">AI checked</p>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <PrismHeroVisual />
        </section>

        <section ref={discoveryRef} id="discover" className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Discover"
            title="Scan an internship opportunity"
            subtitle="Paste the internship post or URL, and Prism AI will analyze it for scam risk."
            right={
              <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200">
                Category: <span className="font-semibold text-white">Internship</span>
              </div>
            }
          />

          <div className="mt-6 space-y-4">
            <div className="rounded-[28px] border border-white/10 bg-slate-950/40 p-6">
              <label className="block text-sm font-semibold text-slate-200 mb-3">Internship Post (Text or URL)</label>
              <textarea
                value={scanInputText}
                onChange={(e) => setScanInputText(e.target.value)}
                placeholder="Paste the internship post text here... or use the URL field below."
                className="w-full rounded-[20px] border border-white/10 bg-slate-900/50 p-4 text-base text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/30 focus:ring-2 focus:ring-cyan-400/20 resize-none"
                rows={5}
              />
            </div>

            <div className="rounded-[28px] border border-white/10 bg-slate-950/40 p-6">
              <label className="block text-sm font-semibold text-slate-200 mb-3">Internship URL (Optional)</label>
              <input
                type="url"
                value={scanInputUrl}
                onChange={(e) => setScanInputUrl(e.target.value)}
                placeholder="https://example.com/internship"
                className="w-full rounded-[20px] border border-white/10 bg-slate-900/50 p-4 text-base text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/30 focus:ring-2 focus:ring-cyan-400/20"
              />
            </div>

            {error && (
              <div className="rounded-[20px] border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleScanSubmit}
                disabled={isLoading || (!scanInputText && !scanInputUrl)}
                className="rounded-full bg-[linear-gradient(135deg,#8b5cf6,#06b6d4)] px-6 py-3 text-sm font-semibold text-white shadow-[0_18px_50px_rgba(34,211,238,0.2)] transition hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader className="h-4 w-4 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Radar className="h-4 w-4" />
                    Start Trust Scan
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  setScanInputText('')
                  setScanInputUrl('')
                  setCurrentScan(null)
                  setError(null)
                }}
                className="rounded-full border border-white/10 bg-white/[0.06] px-6 py-3 text-sm font-semibold text-slate-100 transition hover:border-white/20 hover:bg-white/10"
              >
                Clear
              </button>
            </div>
          </div>
        </section>

        <section ref={historyRef} id="history" className="section-shell p-6 sm:p-8">
          <SectionHeading eyebrow="History" title="Scan History" subtitle="Recent trust scans from this device or account." />

          <div className="mt-6 rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
            <ScanHistory />
          </div>
        </section>

        <section ref={learnRef} id="learn" className="section-shell p-6 sm:p-8">
          <SectionHeading eyebrow="Learn" title="Scam Pattern Library" subtitle="Common internship scam patterns and how to handle them." />
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ScamPatternCard title="Registration Fee Scam" risk="High" example="Pay ₹999 to confirm your slot." advice="Do not pay. Ask for official email and link." />
            <ScamPatternCard title="WhatsApp-only Recruiter" risk="Medium" example="Apply via WhatsApp message" advice="Request official email and company link." />
            <ScamPatternCard title="Guaranteed Selection" risk="High" example="Guaranteed selection, no interview" advice="Be skeptical. Ask for interview process details." />
            <ScamPatternCard title="Fake HR Email" risk="Medium" example="hr.companyname@gmail.com" advice="Verify domain and cross-check LinkedIn." />
            <ScamPatternCard title="Document Harvesting" risk="High" example="Send PAN/Aadhaar to confirm" advice="Never share sensitive documents early." />
            <ScamPatternCard title="Certificate-only Internship" risk="Low" example="Certificate provided, no real work" advice="Ask for past intern work samples." />
          </div>
        </section>

        <section ref={verifyRef} id="verify" className="section-shell p-6 sm:p-8">
          {currentScan ? (
            <div className="space-y-6">
              <SectionHeading
                eyebrow="Verify"
                title="Scan Result"
                subtitle={`Trust Score: ${currentScan.trust_score || 'N/A'} | Risk: ${currentScan.risk_level || 'Analyzing'}`}
              />
              <p className="text-slate-300">{currentScan.summary}</p>
              {currentScan.requires_human_review && (
                <div className="rounded-[28px] border border-orange-400/20 bg-orange-500/10 p-6 space-y-4">
                  <h3 className="text-lg font-semibold text-orange-100">⚠️ Human Review Required</h3>
                  {currentScan.human_review?.options && (
                    <div className="grid gap-2">
                      {currentScan.human_review.options.map((opt) => (
                        <button
                          key={opt}
                          onClick={() => handleReviewDecision(opt)}
                          disabled={isLoading}
                          className="rounded-lg border border-orange-300/30 bg-orange-500/20 px-4 py-2 text-sm font-medium text-orange-100 hover:bg-orange-500/30 disabled:opacity-50"
                        >
                          {opt.replace(/_/g, ' ')}
                        </button>
                      ))}
                    </div>
                  )}
                  <textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Notes..."
                    className="w-full rounded-lg border border-white/10 bg-slate-900/50 p-2 text-sm text-white resize-none"
                    rows={2}
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400">
              <Radar className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Submit an internship to scan</p>
            </div>
          )}
        </section>

        <section className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Results"
            title="Demo Listings"
            subtitle="Browse demo internship listings"
            right={
              <div className="flex flex-wrap gap-2">
                <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-100">
                  Verified
                </span>
                <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
                  AI checked
                </span>
                <span className="rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1.5 text-xs font-semibold text-orange-100">
                  Risk detected
                </span>
              </div>
            }
          />

          <div className="mt-6 grid gap-5 lg:grid-cols-2 2xl:grid-cols-3">
            {listings.map((listing) => (
              <ListingCard
                key={listing.id}
                listing={listing}
                selected={selectedListingId === listing.id}
                saved={isSaved(listing.id)}
                onSelect={() => {
                  setSelectedListingId(listing.id)
                  scrollToSection(verifyRef)
                  setToast(`Selected ${listing.title} for trust review.`)
                }}
                onSave={() => {
                  toggleSave(listing.id)
                  setToast(isSaved(listing.id) ? `${listing.title} removed from saved items.` : `${listing.title} saved for later.`)
                }}
              />
            ))}
          </div>
        </section>

        <section ref={verifyRef} id="verify" className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Verify"
            title="Trust Breakdown"
            subtitle={`Focused on ${selectedListing.title} — ${selectedListing.company}. Prism combines identity, consistency, and scam-pattern signals before you apply.`}
          />

          <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-6">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">Selected result</p>
                  <h3 className="mt-3 text-2xl font-semibold text-white">{selectedListing.title}</h3>
                  <p className="mt-1 text-slate-400">{selectedListing.company}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${trust.className}`}>
                      {trust.label}
                    </span>
                    <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${risk.className}`}>
                      {risk.label}
                    </span>
                  </div>
                </div>
                <ScoreRing score={selectedListing.trustScore} size={172} />
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-[24px] border border-emerald-400/15 bg-emerald-500/[0.08] p-5">
                  <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-emerald-200">
                    <CheckCircle className="h-4 w-4" />
                    Green flags
                  </div>
                  <ul className="space-y-3 text-sm leading-6 text-slate-200">
                    {selectedListing.greenFlags.map((item) => (
                      <li key={item} className="flex items-start gap-3">
                        <span className="mt-1 h-2.5 w-2.5 rounded-full bg-emerald-300 shadow-[0_0_16px_rgba(52,211,153,0.65)]" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-[24px] border border-rose-400/15 bg-rose-500/8 p-5">
                  <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-rose-200">
                    <AlertTriangle className="h-4 w-4" />
                    Red flags
                  </div>
                  <ul className="space-y-3 text-sm leading-6 text-slate-200">
                    {selectedListing.redFlags.map((item) => (
                      <li key={item} className="flex items-start gap-3">
                        <span className="mt-1 h-2.5 w-2.5 rounded-full bg-rose-300 shadow-[0_0_16px_rgba(251,113,133,0.65)]" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
                <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Verification sources</p>
                <div className="grid grid-cols-2 gap-3">
                  {selectedListing.verificationSources.map((source) => (
                    <div key={source} className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-200">
                      {source}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
                <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
                  <Brain className="h-4 w-4 text-violet-300" />
                  AI explanation
                </div>
                <p className="text-sm leading-7 text-slate-200">
                  Prism AI found this internship mostly reliable. The strongest trust signals are the clear stipend, consistent company identity, and absence of payment requests. The only caution is that the company has limited public history, so the user should apply through official links only.
                </p>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
                <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
                  <Radar className="h-4 w-4 text-cyan-300" />
                  Risk pattern detector
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedListing.detectedPatterns.map((pattern) => (
                    <span key={pattern} className="rounded-full border border-emerald-400/15 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-100">
                      {pattern}
                    </span>
                  ))}
                </div>
              </div>

              <LiveAgentTracePanel />
            </div>
          </div>
        </section>

        <section ref={insightsRef} id="insights" className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Insights"
            title="Market Signals"
            subtitle="Prism does not only verify listings. It observes demand, growth, and risk patterns."
          />

          <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {[
              {
                title: 'Demand Density',
                copy: 'Frontend and AI/ML internships are most active this week.',
                icon: Map,
                accent: 'cyan',
                visual: <DensityGrid />,
              },
              {
                title: 'Growth Trend',
                copy: 'AI/ML internships up 32% this month.',
                icon: TrendingUp,
                accent: 'emerald',
                visual: (
                  <div className="mt-3 rounded-3xl border border-white/10 bg-slate-950/40 p-3 text-xs text-slate-400">
                    Week-over-week growth signal
                  </div>
                ),
              },
              {
                title: 'Risk Cluster',
                copy: 'Most suspicious posts came from Telegram and WhatsApp groups.',
                icon: AlertTriangle,
                accent: 'rose',
                visual: (
                  <div className="mt-3 flex items-center gap-3 rounded-3xl border border-rose-400/15 bg-rose-500/10 p-4">
                    <AlertTriangle className="h-5 w-5 text-rose-300" />
                    <span className="text-sm text-slate-100">61% of risky posts</span>
                  </div>
                ),
              },
              {
                title: 'Best Timing',
                copy: 'Apply within 48 hours for better response chances.',
                icon: Clock,
                accent: 'violet',
                visual: (
                  <div className="mt-3 rounded-3xl border border-violet-400/15 bg-violet-500/10 p-4 text-sm text-violet-100">
                    Early applicants get better review placement.
                  </div>
                ),
              },
            ].map((card) => {
              const Icon = card.icon
              const accentClass =
                card.accent === 'cyan'
                  ? 'border-cyan-400/20 bg-cyan-500/10 text-cyan-100'
                  : card.accent === 'emerald'
                    ? 'border-emerald-400/20 bg-emerald-500/10 text-emerald-100'
                    : card.accent === 'rose'
                      ? 'border-rose-400/20 bg-rose-500/10 text-rose-100'
                      : 'border-violet-400/20 bg-violet-500/10 text-violet-100'

              return (
                <article key={card.title} className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className={`inline-flex rounded-2xl border p-3 ${accentClass}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <h3 className="mt-4 text-lg font-semibold text-white">{card.title}</h3>
                    </div>
                    {card.title === 'Growth Trend' ? <TrendingUp className="h-5 w-5 text-emerald-300" /> : null}
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{card.copy}</p>
                  {card.visual}
                </article>
              )
            })}
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <LineChart />
            <RiskDistributionCard />
          </div>
        </section>

        <section ref={recommendationsRef} id="recommendations" className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Recommendations"
            title="Best Match for You"
            subtitle="Prism balances trust, growth, and role quality to surface the safest high-value option."
          />

          <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[30px] border border-emerald-400/20 bg-[linear-gradient(180deg,rgba(16,185,129,0.12),rgba(8,15,34,0.5))] p-6 shadow-[0_24px_80px_rgba(16,185,129,0.08)]">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-100">
                    <BadgeCheck className="h-3.5 w-3.5" />
                    Recommended
                  </p>
                  <h3 className="mt-4 text-3xl font-semibold text-white">Backend Intern — CloudNest</h3>
                  <p className="mt-2 max-w-xl text-sm leading-7 text-slate-300">
                    Highest trust score among paid internships, clear role and responsibilities, verified recruiter profile, strong match for students with project experience, low scam risk, and a healthy growth signal in backend/API roles.
                  </p>
                </div>
                <div className="flex items-center gap-5 rounded-[28px] border border-white/10 bg-slate-950/50 p-4">
                  <ScoreRing score={91} size={154} />
                  <div className="space-y-2 text-sm text-slate-300">
                    <p>
                      <span className="font-semibold text-white">Trust:</span> 91/100
                    </p>
                    <p>
                      <span className="font-semibold text-white">Risk:</span> Low
                    </p>
                    <p>
                      <span className="font-semibold text-white">Confidence:</span> High
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-2">
                {compareReasons.map((reason) => (
                  <div key={reason} className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm text-slate-200">
                    <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                    <span>{reason}</span>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-[24px] border border-white/10 bg-slate-950/45 p-5">
                <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
                  <Brain className="h-4 w-4 text-violet-300" />
                  AI summary
                </div>
                <p className="text-sm leading-7 text-slate-200">
                  Based on trust, stipend clarity, company footprint, and skill growth, CloudNest is the safest high-value option. Nova Labs is also good if you prefer frontend work. Avoid SkillGrow Careers unless the company provides stronger verification.
                </p>
              </div>
            </div>

            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
              {recommendationSummary.map((item) => {
                const accent =
                  item.label === 'Safest Option'
                    ? 'emerald'
                    : item.label === 'Fastest Growing'
                      ? 'violet'
                      : item.label === 'Best Remote Option'
                        ? 'cyan'
                        : 'rose'
                const toneClass =
                  accent === 'emerald'
                    ? 'border-emerald-400/20 bg-emerald-500/10 text-emerald-100'
                    : accent === 'violet'
                      ? 'border-violet-400/20 bg-violet-500/10 text-violet-100'
                      : accent === 'cyan'
                        ? 'border-cyan-400/20 bg-cyan-500/10 text-cyan-100'
                        : 'border-rose-400/20 bg-rose-500/10 text-rose-100'

                return (
                  <article key={item.label} className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
                    <div className={`inline-flex rounded-2xl border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.22em] ${toneClass}`}>
                      {item.label}
                    </div>
                    <h3 className="mt-4 text-lg font-semibold text-white">{item.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{item.detail}</p>
                  </article>
                )
              })}
            </div>
          </div>
        </section>

        <section className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Act"
            title="Next Actions"
            subtitle="Prism moves from discovery to a safer action flow with one-click helpers and lightweight guidance."
          />

          <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <ActionTile
              title="Apply Safely"
              description="Open the safest application path using verified links and a short pre-flight checklist."
              icon={ShieldCheck}
              buttonLabel="Open safe flow"
              accent="emerald"
              onClick={() => setToast('Safe application flow prepared with verified links.')}
            />
            <ActionTile
              title="Generate Cover Message"
              description="Create a polite message that asks for official process, stipend details, responsibilities, and fees."
              icon={Send}
              buttonLabel="Generate message"
              accent="violet"
              onClick={() => setModalMode('cover')}
            />
            <ActionTile
              title="Save Deadline"
              description="Bookmark the deadline and keep the internship on your shortlist for later review."
              icon={Clock}
              buttonLabel="Save reminder"
              accent="cyan"
              onClick={() => setToast('Deadline saved in the demo shortlist.')}
            />
            <ActionTile
              title="Compare with Another Internship"
              description="Open a side-by-side trust comparison to see which listing is safer and more valuable."
              icon={TrendingUp}
              buttonLabel="Compare options"
              accent="amber"
              onClick={() => setToast('Comparison workspace opened for the selected internships.')}
            />
            <ActionTile
              title="Report Suspicious Listing"
              description="Flag fake signals, payment requests, or suspicious contact paths for review."
              icon={AlertTriangle}
              buttonLabel="Flag listing"
              accent="rose"
              onClick={() => setToast('Suspicious listing report drafted from trust signals.')}
            />
            <ActionTile
              title="Create Application Checklist"
              description="Get a fake but useful checklist that keeps the application process safe and organized."
              icon={Brain}
              buttonLabel="Open checklist"
              accent="emerald"
              onClick={() => setModalMode('checklist')}
            />
          </div>
        </section>

        <section className="section-shell p-6 sm:p-8">
          <SectionHeading
            eyebrow="Reuse"
            title="One trust engine. Many use cases."
            subtitle="The same Prism workflow can adapt to housing, scholarships, events, and local services without changing the core trust model."
          />

          <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {categoryPresets.map((preset) => (
              <CategoryCard
                key={preset.name}
                title={preset.name}
                subtitle={preset.subtitle}
                description={preset.description}
                selected={selectedCategory === preset.name}
                onClick={() => {
                  setSelectedCategory(preset.name)
                  setToast(`${preset.name} preset previewed.`)
                }}
              />
            ))}
          </div>

          <div className="mt-6 rounded-[28px] border border-white/10 bg-slate-950/45 p-5 text-sm leading-7 text-slate-300">
            Prism AI is built to act like a startup product demo: one trust engine, many domains, and a clear flow from discovery to verification to recommendation to action.
          </div>
        </section>

        <footer className="flex flex-col gap-4 border-t border-white/10 pt-6 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
          <p>Prism AI — AI trust radar for smarter decisions.</p>
          <div className="flex flex-wrap gap-4">
            {['Privacy', 'Trust Signals', 'Report Scam', 'Contact'].map((link) => (
              <a key={link} href="#" className="transition hover:text-white">
                {link}
              </a>
            ))}
          </div>
        </footer>
      </div>

      <Modal
        mode={modalMode}
        title={modalMode === 'cover' ? 'Safe Application Message' : 'Application Checklist'}
        listingTitle={selectedListing.title}
        listingCompany={selectedListing.company}
        onClose={() => setModalMode(null)}
      />
      <Toast message={toastMessage} />
    </div>
  )
}
