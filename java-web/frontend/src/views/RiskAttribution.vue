<script setup lang="ts">
import { computed } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js'
import { usePortfolioStore } from '../stores/portfolio'
import PortfolioInput from '../components/PortfolioInput.vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

const store = usePortfolioStore()
const r = computed(() => store.riskResult)

const riskBarData = computed(() => {
  if (!r.value) return null
  const sorted = [...r.value.holdings].sort((a, b) => b.ctr_pct - a.ctr_pct)
  return {
    labels: sorted.map(h => h.ticker),
    datasets: [{
      label: '% of Total Risk',
      data: sorted.map(h => h.ctr_pct),
      backgroundColor: 'rgba(200, 137, 62, 0.7)',
      borderRadius: 6,
    }],
  }
})

const riskBarOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  plugins: { legend: { display: false }, title: { display: true, text: 'Risk Contribution by Holding' } },
  scales: { x: { title: { display: true, text: '% of Total Risk' } } },
}

const sysPieData = computed(() => {
  if (!r.value) return null
  return {
    labels: ['Systematic', 'Idiosyncratic'],
    datasets: [{
      data: [r.value.systematic_pct, r.value.idiosyncratic_pct],
      backgroundColor: ['rgba(23, 63, 58, 0.8)', 'rgba(200, 137, 62, 0.6)'],
    }],
  }
})
</script>

<template>
  <div>
    <div class="fc-section-header mb-4">
      <div class="fc-bar"></div>
      <h1>Risk Attribution</h1>
    </div>

    <PortfolioInput @submit="store.runRiskAttribution()" />

    <div v-if="store.loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>
    <div v-if="store.error" class="alert alert-error mb-4"><span>{{ store.error }}</span></div>

    <template v-if="r">
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Annualized Vol</div>
          <div class="text-2xl font-bold">{{ r.total_vol_annual.toFixed(2) }}%</div>
        </div>
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">VaR (95%)</div>
          <div class="text-2xl font-bold text-error">{{ r.var_95.toFixed(2) }}%</div>
        </div>
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Systematic Risk</div>
          <div class="text-2xl font-bold">{{ r.systematic_pct.toFixed(0) }}%</div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="fc-card">
          <Bar v-if="riskBarData" :data="riskBarData" :options="riskBarOptions" />
        </div>
        <div class="fc-card flex items-center justify-center">
          <div class="w-64">
            <Doughnut v-if="sysPieData" :data="sysPieData" :options="{ plugins: { title: { display: true, text: 'Systematic vs Idiosyncratic' } } }" />
          </div>
        </div>
      </div>

      <!-- Holdings table -->
      <div class="fc-card">
        <h3 class="font-bold text-sm mb-3 opacity-70">Holdings Risk Contribution</h3>
        <div class="overflow-x-auto">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Weight</th>
                <th>MCTR</th>
                <th>CTR</th>
                <th>% of Risk</th>
                <th>Sector</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in r.holdings" :key="h.ticker">
                <td class="font-mono font-bold">{{ h.ticker }}</td>
                <td>{{ h.weight.toFixed(1) }}%</td>
                <td>{{ h.mctr.toFixed(4) }}</td>
                <td>{{ h.ctr.toFixed(4) }}</td>
                <td class="font-semibold">{{ h.ctr_pct.toFixed(1) }}%</td>
                <td class="opacity-60">{{ h.sector }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Factor exposures -->
      <div class="fc-card mt-4">
        <h3 class="font-bold text-sm mb-3 opacity-70">Factor Risk Contribution</h3>
        <div class="overflow-x-auto">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Factor</th>
                <th>Portfolio Exposure</th>
                <th>Variance Contribution</th>
                <th>% of Systematic</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in r.factors" :key="f.factor">
                <td class="font-mono font-bold">{{ f.factor }}</td>
                <td>{{ f.exposure.toFixed(4) }}</td>
                <td>{{ f.variance_contribution.toFixed(6) }}</td>
                <td class="font-semibold">{{ f.pct_of_systematic.toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
