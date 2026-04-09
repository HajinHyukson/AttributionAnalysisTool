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
  const performanceResult = ref<PerformanceAttributionResult | null>(null)
  const stressResult = ref<StressTestResult | null>(null)
  const correlationResult = ref<CorrelationRegimeResult | null>(null)

  function setPortfolio(p: string) {
    portfolio.value = p
    api.savePortfolio(p)
  }

  async function runRiskAttribution() {
    loading.value = true
    error.value = null
    try {
      riskResult.value = await api.riskAttribution({
        portfolio: portfolio.value,
        years: years.value,
        benchmark: benchmark.value,
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runPerformanceAttribution() {
    loading.value = true
    error.value = null
    try {
      performanceResult.value = await api.performanceAttribution({
        portfolio: portfolio.value,
        years: years.value,
        benchmark: benchmark.value,
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runStressTest() {
    loading.value = true
    error.value = null
    try {
      stressResult.value = await api.stressTest({
        portfolio: portfolio.value,
        years: Math.max(years.value, 5),
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function runCorrelationRegime() {
    loading.value = true
    error.value = null
    try {
      correlationResult.value = await api.correlationRegime({
        portfolio: portfolio.value,
        years: years.value,
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  return {
    portfolio, years, benchmark, loading, error,
    riskResult, performanceResult, stressResult, correlationResult,
    setPortfolio,
    runRiskAttribution, runPerformanceAttribution,
    runStressTest, runCorrelationRegime,
  }
})
