<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { usePortfolioStore } from '../stores/portfolio'
import PortfolioInput from '../components/PortfolioInput.vue'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const store = usePortfolioStore()
const c = computed(() => store.correlationResult)

const corrLineData = computed(() => {
  if (!c.value || !c.value.rolling_avg_correlation.length) return null
  // Downsample to max 200 points for readability
  const raw = c.value.rolling_avg_correlation
  const step = Math.max(1, Math.floor(raw.length / 200))
  const sampled = raw.filter((_, i) => i % step === 0)
  return {
    labels: sampled.map(p => p.date),
    datasets: [{
      label: 'Avg Pairwise Correlation',
      data: sampled.map(p => p.value),
      borderColor: 'rgba(23, 63, 58, 0.8)',
      fill: false,
      tension: 0.3,
      pointRadius: 0,
    }],
  }
})

const divRatioData = computed(() => {
  if (!c.value || !c.value.diversification_ratio.length) return null
  const raw = c.value.diversification_ratio
  const step = Math.max(1, Math.floor(raw.length / 200))
  const sampled = raw.filter((_, i) => i % step === 0)
  return {
    labels: sampled.map(p => p.date),
    datasets: [{
      label: 'Diversification Ratio',
      data: sampled.map(p => p.value),
      borderColor: 'rgba(200, 137, 62, 0.8)',
      fill: false,
      tension: 0.3,
      pointRadius: 0,
    }],
  }
})

const pc1Data = computed(() => {
  if (!c.value || !c.value.pc1_variance_explained.length) return null
  const raw = c.value.pc1_variance_explained
  const step = Math.max(1, Math.floor(raw.length / 200))
  const sampled = raw.filter((_, i) => i % step === 0)
  return {
    labels: sampled.map(p => p.date),
    datasets: [{
      label: 'PC1 Variance Explained (%)',
      data: sampled.map(p => p.value),
      borderColor: 'rgba(122, 46, 46, 0.8)',
      fill: false,
      tension: 0.3,
      pointRadius: 0,
    }],
  }
})

function cellColor(val: number): string {
  if (val >= 0.7) return 'bg-error/30'
  if (val >= 0.4) return 'bg-warning/20'
  if (val <= -0.3) return 'bg-info/20'
  return ''
}
</script>

<template>
  <div>
    <div class="fc-section-header mb-4">
      <div class="fc-bar"></div>
      <h1>Correlation Regime</h1>
    </div>

    <PortfolioInput @submit="store.runCorrelationRegime()" />

    <div v-if="store.loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>
    <div v-if="store.error" class="alert alert-error mb-4"><span>{{ store.error }}</span></div>

    <template v-if="c">
      <!-- Summary -->
      <div class="grid grid-cols-2 gap-3 mb-6">
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Avg Pairwise Correlation</div>
          <div class="text-2xl font-bold">{{ c.current_avg_correlation.toFixed(3) }}</div>
        </div>
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Regime Alerts</div>
          <div class="text-2xl font-bold" :class="c.alerts.length > 0 ? 'text-warning' : 'text-success'">
            {{ c.alerts.length }}
          </div>
        </div>
      </div>

      <!-- Alerts -->
      <div v-if="c.alerts.length" class="mb-4">
        <div v-for="alert in c.alerts.slice(-5)" :key="alert.date"
             :class="['alert mb-2', alert.level === 'critical' ? 'alert-error' : 'alert-warning']">
          <span>{{ alert.date }}: Correlation regime {{ alert.level }} (z-score: {{ alert.z_score }}, avg corr: {{ alert.avg_correlation }})</span>
        </div>
      </div>

      <!-- Correlation heatmap -->
      <div class="fc-card mb-4">
        <h3 class="font-bold text-sm mb-3 opacity-70">Correlation Matrix</h3>
        <div class="overflow-x-auto">
          <table class="table table-sm">
            <thead>
              <tr>
                <th></th>
                <th v-for="t in c.tickers" :key="t" class="font-mono text-xs">{{ t }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in c.current_matrix" :key="c.tickers[i]">
                <td class="font-mono font-bold text-xs">{{ c.tickers[i] }}</td>
                <td v-for="(val, j) in row" :key="j"
                    :class="['text-center text-xs', i === j ? 'opacity-30' : cellColor(val)]">
                  {{ val.toFixed(2) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 gap-4">
        <div class="fc-card">
          <Line v-if="corrLineData" :data="corrLineData"
                :options="{ responsive: true, plugins: { title: { display: true, text: 'Rolling Average Correlation' } }, scales: { x: { display: false } } }" />
        </div>
        <div class="fc-card">
          <Line v-if="divRatioData" :data="divRatioData"
                :options="{ responsive: true, plugins: { title: { display: true, text: 'Diversification Ratio (higher = more diversified)' } }, scales: { x: { display: false } } }" />
        </div>
        <div class="fc-card">
          <Line v-if="pc1Data" :data="pc1Data"
                :options="{ responsive: true, plugins: { title: { display: true, text: 'PC1 Variance Explained (>60% = risk-on/risk-off regime)' } }, scales: { x: { display: false } } }" />
        </div>
      </div>
    </template>
  </div>
</template>
