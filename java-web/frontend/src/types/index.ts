export interface AnalysisRequest {
  portfolio: string
  years?: number
  benchmark?: string
  cache?: boolean
  nFactors?: number
  window?: number
  scenarios?: string
}

export interface HoldingRisk {
  ticker: string
  weight: number
  mctr: number
  ctr: number
  ctr_pct: number
  sector: string
}

export interface FactorRisk {
  factor: string
  exposure: number
  variance_contribution: number
  pct_of_systematic: number
}

export interface RiskAttributionResult {
  total_vol_annual: number
  var_95: number
  holdings: HoldingRisk[]
  factors: FactorRisk[]
  systematic_pct: number
  idiosyncratic_pct: number
  factor_betas: Record<string, Record<string, number>>
}

export interface SectorAttribution {
  sector: string
  portfolio_weight: number
  benchmark_weight: number
  portfolio_return: number
  benchmark_return: number
  allocation_effect: number
  selection_effect: number
  interaction_effect: number
}

export interface SinglePeriodAttribution {
  sectors: SectorAttribution[]
  total_allocation: number
  total_selection: number
  total_interaction: number
  active_return: number
  portfolio_return: number
  benchmark_return: number
}

export interface PeriodAttribution {
  period: string
  portfolio_return: number
  benchmark_return: number
  active_return: number
  allocation: number
  selection: number
  interaction: number
  cumulative_allocation: number
  cumulative_selection: number
  cumulative_interaction: number
  cumulative_active: number
}

export interface PerformanceAttributionResult {
  single_period: SinglePeriodAttribution
  multi_period: {
    periods: PeriodAttribution[]
    cumulative: {
      allocation: number
      selection: number
      interaction: number
      active_return: number
    }
  }
}

export interface ScenarioHolding {
  ticker: string
  weight: number
  return_pct: number
  pnl_contribution_pct: number
  data_available: boolean
}

export interface ScenarioResult {
  name: string
  label: string
  description: string
  start: string
  end: string
  total_pnl_pct: number
  holdings: ScenarioHolding[]
  data_available: boolean
}

export interface StressTestResult {
  scenarios: ScenarioResult[]
  reverse_stress: {
    target_loss_pct: number
    required_market_shock_pct: number
  }
}

export interface TimeSeriesPoint {
  date: string
  value: number
}

export interface CorrelationAlert {
  date: string
  avg_correlation: number
  z_score: number
  level: 'warning' | 'critical'
}

export interface CorrelationRegimeResult {
  current_matrix: number[][]
  tickers: string[]
  current_avg_correlation: number
  rolling_avg_correlation: TimeSeriesPoint[]
  diversification_ratio: TimeSeriesPoint[]
  pc1_variance_explained: TimeSeriesPoint[]
  alerts: CorrelationAlert[]
}
