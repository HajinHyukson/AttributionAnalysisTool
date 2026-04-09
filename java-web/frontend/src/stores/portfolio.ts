import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type {
  RiskAttributionResult,
  PerformanceAttributionResult,
  StressTestResult,
  CorrelationRegimeResult,
} from '../types'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolio = ref('')
  const years = ref(3)
  const benchmark = ref('SPY')
  const loading = ref(false)
  const error = ref<string | null>(null)

  const riskResult = ref<RiskAttributionResult | null>(null)
  const riskError = ref<string | null>(null)
  const performanceResult = ref<PerformanceAttributionResult | null>(null)
  const performanceError = ref<string | null>(null)
  const stressResult = ref<StressTestResult | null>(null)
  const stressError = ref<string | null>(null)
  const correlationResult = ref<CorrelationRegimeResult | null>(null)
  const correlationError = ref<string | null>(null)

  function setPortfolio(p: string) {
    portfolio.value = p
    api.savePortfolio(p)
  }

  async function runRiskAttribution() {
    loading.value = true
    riskError.value = null
    try {
      riskResult.value = await api.riskAttribution({
        portfolio: portfolio.value,
        years: years.value,
        benchmark: benchmark.value,
      })
    } catch (e: unknown) {
      riskError.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runPerformanceAttribution() {
    loading.value = true
    performanceError.value = null
    try {
      performanceResult.value = await api.performanceAttribution({
        portfolio: portfolio.value,
        years: years.value,
        benchmark: benchmark.value,
      })
    } catch (e: unknown) {
      performanceError.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runStressTest() {
    loading.value = true
    stressError.value = null
    try {
      stressResult.value = await api.stressTest({
        portfolio: portfolio.value,
        years: Math.max(years.value, 5),
      })
    } catch (e: unknown) {
      stressError.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runCorrelationRegime() {
    loading.value = true
    correlationError.value = null
    try {
      correlationResult.value = await api.correlationRegime({
        portfolio: portfolio.value,
        years: years.value,
      })
    } catch (e: unknown) {
      correlationError.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runAll() {
    loading.value = true
    error.value = null
    riskError.value = null
    performanceError.value = null
    stressError.value = null
    correlationError.value = null

    const results = await Promise.allSettled([
      (async () => {
        riskResult.value = await api.riskAttribution({
          portfolio: portfolio.value, years: years.value, benchmark: benchmark.value,
        })
      })(),
      (async () => {
        performanceResult.value = await api.performanceAttribution({
          portfolio: portfolio.value, years: years.value, benchmark: benchmark.value,
        })
      })(),
      (async () => {
        stressResult.value = await api.stressTest({
          portfolio: portfolio.value, years: Math.max(years.value, 5),
        })
      })(),
      (async () => {
        correlationResult.value = await api.correlationRegime({
          portfolio: portfolio.value, years: years.value,
        })
      })(),
    ])

    const labels = ['Risk Attribution', 'Performance Attribution', 'Stress Test', 'Correlation Regime']
    const errors: string[] = []
    results.forEach((r, i) => {
      if (r.status === 'rejected') {
        const msg = r.reason instanceof Error ? r.reason.message : String(r.reason)
        errors.push(`${labels[i]}: ${msg}`)
        if (i === 0) riskError.value = msg
        if (i === 1) performanceError.value = msg
        if (i === 2) stressError.value = msg
        if (i === 3) correlationError.value = msg
      }
    })

    // Only show global error if ALL failed
    if (errors.length === results.length) {
      error.value = errors.join('\n')
    } else if (errors.length > 0) {
      error.value = null // Partial success — show per-module errors instead
    }

    loading.value = false
  }

  return {
    portfolio, years, benchmark, loading, error,
    riskResult, riskError,
    performanceResult, performanceError,
    stressResult, stressError,
    correlationResult, correlationError,
    setPortfolio, runAll,
    runRiskAttribution, runPerformanceAttribution,
    runStressTest, runCorrelationRegime,
  }
})
