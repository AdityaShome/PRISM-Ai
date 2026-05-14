const ENV_API_URL = import.meta.env.VITE_API_URL?.trim()
const FALLBACK_BASE_URLS = [ENV_API_URL, 'http://localhost:8001', 'http://localhost:8000'].filter(Boolean) as string[]
export const API_BASE_CANDIDATES = FALLBACK_BASE_URLS

export type ScanStatus = 'completed' | 'awaiting_human_review' | 'pending' | 'running' | 'failed' | 'rejected'

export interface HumanReviewPayload {
  type?: string
  scan_id?: string
  message: string
  review_reasons: string[]
  options: string[]
  trust_score?: number
  risk_level?: string
  confidence?: string
  green_flags?: Array<{ label: string; evidence: string; severity?: string }>
  red_flags?: Array<{ label: string; evidence: string; severity?: string }>
  missing_information?: string[]
}

export interface AgentTraceStep {
  step: string
  label: string
  status: string
  detail: string
  timestamp: string
}

export interface ScanListItem {
  id: string
  created_at: string
  risk_level: string
  trust_score: number
  summary?: string | null
  extracted_title?: string | null
  extracted_company?: string | null
  category: string
  workflow_status?: string
}

export interface ScanResponse {
  scan_id: string
  category?: string
  workflow_status: ScanStatus | string
  requires_human_review: boolean
  human_review?: HumanReviewPayload | null
  human_review_reason?: string[]
  human_decision?: string | null
  human_notes?: string | null
  trust_score?: number
  scam_likelihood?: number
  risk_level?: string
  confidence?: string
  summary?: string
  extracted_details?: Record<string, unknown>
  green_flags?: Array<{ label: string; evidence: string; severity?: string }>
  red_flags?: Array<{ label: string; evidence: string; severity?: string }>
  missing_information?: string[]
  verification_signals?: Record<string, unknown>
  score_breakdown?: Array<{ label: string; impact: number; reason: string }>
  recommended_action?: string
  safe_message?: string
  agent_trace?: AgentTraceStep[]
  final_result?: Record<string, unknown>
  source_results?: Record<string, unknown> | null
  company_verification_sources?: Array<{ title: string; url?: string; snippet?: string; source_type?: string }>
  review_requested_at?: string | null
  review_completed_at?: string | null
}

export interface ScanCreatePayload {
  text?: string | null
  url?: string | null
  category?: string
  source_type?: string
  company_name?: string | null
  role_title?: string | null
  stipend?: string | null
  contact_method?: string | null
}

export interface ReviewDecisionPayload {
  decision: 'run_deeper_scan' | 'generate_safe_message' | 'mark_suspicious' | 'continue_anyway' | 'reject_opportunity' | string
  notes?: string | null
}

export interface FeedbackPayload {
  scan_id: string
  user_rating: 'helpful' | 'not_helpful' | string
  actual_outcome?: string | null
  user_comment?: string | null
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  let lastError: unknown = null

  for (const baseUrl of FALLBACK_BASE_URLS) {
    try {
      const response = await fetch(`${baseUrl}${path}`, init)
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || payload.message || `Request failed: ${response.status} ${response.statusText}`)
      }
      return (await response.json()) as T
    } catch (error) {
      lastError = error
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Prism AI backend is unavailable')
}

export async function createScan(payload: ScanCreatePayload): Promise<ScanResponse> {
  if (!payload.text && !payload.url) {
    throw new Error('Either text or URL is required')
  }

  return fetchJson<ScanResponse>('/api/scans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: payload.text ?? null,
      url: payload.url ?? null,
      category: payload.category ?? 'internship',
      source_type: payload.source_type ?? null,
    }),
  })
}

export async function getScan(scanId: string): Promise<ScanResponse> {
  return fetchJson<ScanResponse>(`/api/scans/${scanId}`)
}

export async function listScans(): Promise<ScanListItem[]> {
  const response = await fetchJson<{ items: ScanListItem[] }>('/api/scans')
  return response.items || []
}

export async function submitReview(scanId: string, decision: ReviewDecisionPayload['decision'], notes: string | null = null): Promise<ScanResponse> {
  return fetchJson<ScanResponse>(`/api/scans/${scanId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, notes: notes || null }),
  })
}

export async function submitFeedback(payload: FeedbackPayload): Promise<{ id: string; scan_id: string }> {
  return fetchJson<{ id: string; scan_id: string }>('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function getHealth(): Promise<{ status: string }> {
  return fetchJson<{ status: string }>('/health')
}

// Backwards-compatible exports for existing components.
export const startScan = (text: string | null, url: string | null, category = 'internship') =>
  createScan({ text, url, category })

export const getScans = () => listScans()