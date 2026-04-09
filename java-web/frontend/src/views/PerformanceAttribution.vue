<script setup lang="ts">
import { computed } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { usePortfolioStore } from '../stores/portfolio'
import PortfolioInput from '../components/PortfolioInput.vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend)

const store = usePortfolioStore()
const p = computed(() => store.performanceResult)

const waterfallData = computed(() => {
  if (!p.value) return null
  const sp = p.value.single_period
  return {
    labels: ['Allocation', 'Selection', 'Interaction', 'Active Return'],
    datasets: [{
      label: 'Effect (%)',
      data: [sp.total_allocation, sp.total_selection, sp.total_interaction, sp.active_return],
      backgroundColor: [
        sp.total_allocation >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)',
        sp.total_selection >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)',
        sp.total_interaction >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)',
        sp.active_return >= 0 ? 'rgba(23, 63, 58, 0.8)' : 'rgba(200, 50, 50, 0.8)',
      ],
      borderRadius: 6,
    }],
  }
})

const cumulativeData = computed(() => {
  if (!p.value || !p.value.multi_period.periods.length) return null
  const periods = p.value.multi_period.periods
  return {
    labels: periods.map(p => p.period),
    datasets: [
      { label: 'Allocation', data: periods.map(p => p.cumulative_allocation), borderColor: 'rgba(23, 63, 58, 0.8)', fill: false, tension: 0.3 },
      { label: 'Selection', data: periods.map(p => p.cumulative_selection), borderColor: 'rgba(200, 137, 62, 0.8)', fill: false, tension: 0.3 },
      { label: 'Active Return', data: periods.map(p => p.cumulative_active), borderColor: 'rgba(122, 46, 46, 0.8)', fill: false, tension: 0.3, borderWidth: 2 },
    ],
  }
})
</script>

<template>
  <div>
    <div class="fc-section-header mb-4">
      <div class="fc-bar"></div>
      <h1>Performance Attribution</h1>
    </div>

    <PortfolioInput @submit="store.runPerformanceAttribution()" />

    <div v-if="store.loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>
    <div v-if="store.error" class="alert alert-error mb-4"><span>{{ store.error }}</span></div>

    <template v-if="p">
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Portfolio Return</div>
          <div class="text-xl font-bold" :class="p.single_period.portfolio_return >= 0 ? 'text-success' : 'text-error'">
            {{ p.single_period.portfolio_return.toFixed(2) }}%
          </div>
        </div>
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Benchmark Return</div>
          <div class="text-xl font-bold">{{ p.single_period.benchmark_return.toFixed(2) }}%</div>
        </div>
        <div class="fc-card-compact text-center">
          <div class="text-xs font-semibold opacity-50 uppercase">Active Return</div>
          <div class="text-xl font-bold" :class="p.single_period.active_return >= 0 ? 'text-success' : 'text-error'">
            {{ p.single_period.active_return.toFixed(2) }}%
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="fc-card">
          <Bar v-if="waterfallData" :data="waterfallData"
               :options="{ responsive: true, plugins: { title: { display: true, text: 'Brinson-Fachler Attribution' }, legend: { display: false } } }" />
        </div>
        <div class="fc-card">
          <Line v-if="cumulativeData" :data="cumulativeData"
                :options="{ responsive: true, plugins: { title: { display: true, text: 'Cumulative Attribution' } }, scales: { y: { title: { display: true, text: '%' } } } }" />
        </div>
      </div>

      <!-- Sector attribution table -->
      <div class="fc-card">
        <h3 class="font-bold text-sm mb-3 opacity-70">Sector Attribution</h3>
        <div class="overflow-x-auto">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Sector</th>
                <th>Port Wt</th>
                <th>Bench Wt</th>
                <th>Port Ret</th>
                <th>Bench Ret</th>
                <th>Allocation</th>
                <th>Selection</th>
                <th>Interaction</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in p.single_period.sectors" :key="s.sector">
                <td class="font-semibold">{{ s.sector }}</td>
                <td>{{ s.portfolio_weight.toFixed(1) }}%</td>
                <td>{{ s.benchmark_weight.toFixed(1) }}%</td>
                <td :class="s.portfolio_return >= 0 ? 'text-success' : 'text-error'">{{ s.portfolio_return.toFixed(2) }}%</td>
                <td>{{ s.benchmark_return.toFixed(2) }}%</td>
                <td :class="s.allocation_effect >= 0 ? 'text-success' : 'text-error'">{{ s.allocation_effect.toFixed(2) }}%</td>
                <td :class="s.selection_effect >= 0 ? 'text-success' : 'text-error'">{{ s.selection_effect.toFixed(2) }}%</td>
                <td :class="s.interaction_effect >= 0 ? 'text-success' : 'text-error'">{{ s.interaction_effect.toFixed(2) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
