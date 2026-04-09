<script setup lang="ts">
import { usePortfolioStore } from '../stores/portfolio'
import PortfolioInput from '../components/PortfolioInput.vue'

const store = usePortfolioStore()

async function runAll() {
  await Promise.all([
    store.runRiskAttribution(),
    store.runPerformanceAttribution(),
    store.runStressTest(),
    store.runCorrelationRegime(),
  ])
}
</script>

<template>
  <div>
    <div class="fc-section-header mb-6">
      <div class="fc-bar"></div>
      <h1>Attribution Analysis Tool</h1>
    </div>

    <PortfolioInput @submit="runAll" />

    <div v-if="store.loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
      <p class="mt-3 text-sm opacity-60">Running analytics...</p>
    </div>

    <div v-if="store.error" class="alert alert-error mb-4">
      <span>{{ store.error }}</span>
    </div>

    <!-- Summary cards when results are available -->
    <div v-if="store.riskResult" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">Portfolio Vol</div>
        <div class="text-2xl font-bold mt-1">{{ store.riskResult.total_vol_annual.toFixed(1) }}%</div>
      </div>
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">VaR (95%)</div>
        <div class="text-2xl font-bold mt-1">{{ store.riskResult.var_95.toFixed(1) }}%</div>
      </div>
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">Systematic</div>
        <div class="text-2xl font-bold mt-1">{{ store.riskResult.systematic_pct.toFixed(0) }}%</div>
      </div>
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">Holdings</div>
        <div class="text-2xl font-bold mt-1">{{ store.riskResult.holdings.length }}</div>
      </div>
    </div>

    <div v-if="store.performanceResult" class="grid grid-cols-3 gap-3 mb-6">
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">Portfolio Return</div>
        <div class="text-xl font-bold mt-1" :class="store.performanceResult.single_period.portfolio_return >= 0 ? 'text-success' : 'text-error'">
          {{ store.performanceResult.single_period.portfolio_return.toFixed(2) }}%
        </div>
      </div>
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">Benchmark Return</div>
        <div class="text-xl font-bold mt-1">{{ store.performanceResult.single_period.benchmark_return.toFixed(2) }}%</div>
      </div>
      <div class="fc-card-compact text-center">
        <div class="text-xs font-semibold opacity-50 uppercase tracking-wider">Active Return</div>
        <div class="text-xl font-bold mt-1" :class="store.performanceResult.single_period.active_return >= 0 ? 'text-success' : 'text-error'">
          {{ store.performanceResult.single_period.active_return.toFixed(2) }}%
        </div>
      </div>
    </div>

    <div v-if="store.correlationResult" class="fc-card-compact mb-4">
      <div class="text-xs font-semibold opacity-50 uppercase tracking-wider mb-1">Avg Correlation</div>
      <div class="text-lg font-bold">{{ store.correlationResult.current_avg_correlation.toFixed(3) }}</div>
      <div v-if="store.correlationResult.alerts.length" class="mt-2">
        <div v-for="alert in store.correlationResult.alerts.slice(-3)" :key="alert.date"
             :class="['badge badge-sm', alert.level === 'critical' ? 'badge-error' : 'badge-warning']">
          {{ alert.level }}: z={{ alert.z_score }} on {{ alert.date }}
        </div>
      </div>
    </div>

    <!-- Placeholder when no results -->
    <div v-if="!store.riskResult && !store.loading && !store.error" class="text-center py-16 opacity-50">
      <p class="text-lg">Enter your portfolio above and click Analyze</p>
      <p class="text-sm mt-2">Example: AAPL:30, MSFT:25, GOOGL:20, JNJ:15, XOM:10</p>
    </div>
  </div>
</template>
