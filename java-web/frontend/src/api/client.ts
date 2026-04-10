import type {
  AnalysisRequest,
  RiskAttributionResult,
  PerformanceAttributionResult,
  StressTestResult,
  CorrelationRegimeResult,
} from '../types'

async function post<T>(url: string, body: AnalysisRequest): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    const msg = err.details || err.error || res.statusText
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  savePortfolio(portfolio: string) {
    return fetch('/api/portfolio/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ portfolio }),
    })
  },

  riskAttribution(req: AnalysisRequest) {
    return post<RiskAttributionResult>('/api/risk/attribution', req)
  },

  performanceAttribution(req: AnalysisRequest) {
    return post<PerformanceAttributionResult>('/api/performance/attribution', req)
  },

  stressTest(req: AnalysisRequest) {
    return post<StressTestResult>('/api/stress/test', req)
  },

  correlationRegime(req: AnalysisRequest) {
    return post<CorrelationRegimeResult>('/api/correlation/regime', req)
  },
}
