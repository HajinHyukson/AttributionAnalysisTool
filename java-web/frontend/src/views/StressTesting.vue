<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { usePortfolioStore } from '../stores/portfolio'
import PortfolioInput from '../components/PortfolioInput.vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const store = usePortfolioStore()
const s = computed(() => store.stressResult)

const scenarioBarData = computed(() => {
  if (!s.value) return null
  const available = s.value.scenarios.filter(sc => sc.data_available)
  return {
    labels: available.map(sc => sc.label),
    datasets: [{
      label: 'Portfolio Impact (%)',
      data: available.map(sc => sc.total_pnl_pct),
      backgroundColor: available.map(sc => sc.total_pnl_pct >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)'),
      borderRadius: 6,
    }],
  }
})
</script>

<template>
  <div>
    <div class="fc-section-header mb-4">
      <div class="fc-bar"></div>
      <h1>Stress Testing</h1>
    </div>

    <PortfolioInput @submit="store.runStressTest()" />

    <div v-if="store.loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>
    <div v-if="store.error" class="alert alert-error mb-4"><span>{{ store.error }}</span></div>

    <template v-if="s">
      <!-- Scenario summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <div v-for="sc in s.scenarios" :key="sc.name" class="fc-card-compact">
          <div class="text-xs font-semibold opacity-50 uppercase">{{ sc.label }}</div>
          <div class="text-xs opacity-40 mb-2">{{ sc.description }}</div>
          <div v-if="sc.data_available" class="text-2xl font-bold"
               :class="sc.total_pnl_pct >= 0 ? 'text-success' : 'text-error'">
            {{ sc.total_pnl_pct.toFixed(1) }}%
          </div>
          <div v-else class="text-sm opacity-40">No data for this period</div>
          <div class="text-xs opacity-40 mt-1">{{ sc.start }} to {{ sc.end }}</div>
        </div>
      </div>

      <!-- Scenario bar chart -->
      <div class="fc-card mb-6">
        <Bar v-if="scenarioBarData" :data="scenarioBarData"
             :options="{ responsive: true, plugins: { title: { display: true, text: 'Scenario Impact' }, legend: { display: false } }, scales: { y: { title: { display: true, text: 'Portfolio P&L (%)' } } } }" />
      </div>

      <!-- Reverse stress test -->
      <div class="fc-card-compact mb-6">
        <div class="text-xs font-semibold opacity-50 uppercase">Reverse Stress Test</div>
        <p class="mt-2">
          A market decline of
          <span class="font-bold text-error text-lg">{{ s.reverse_stress.required_market_shock_pct.toFixed(1) }}%</span>
          would cause a
          <span class="font-bold">{{ s.reverse_stress.target_loss_pct }}%</span>
          portfolio loss.
        </p>
      </div>

      <!-- Per-holding impact tables -->
      <div v-for="sc in s.scenarios.filter(x => x.data_available)" :key="sc.name" class="fc-card mb-4">
        <h3 class="font-bold text-sm mb-3 opacity-70">{{ sc.label }} — Per-Holding Impact</h3>
        <div class="overflow-x-auto">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Weight</th>
                <th>Return</th>
                <th>P&L Contribution</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in sc.holdings" :key="h.ticker">
                <td class="font-mono font-bold">{{ h.ticker }}</td>
                <td>{{ h.weight.toFixed(1) }}%</td>
                <td :class="h.return_pct >= 0 ? 'text-success' : 'text-error'">{{ h.return_pct.toFixed(1) }}%</td>
                <td :class="h.pnl_contribution_pct >= 0 ? 'text-success' : 'text-error'" class="font-semibold">
                  {{ h.pnl_contribution_pct.toFixed(2) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
