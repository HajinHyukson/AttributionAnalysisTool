<script setup lang="ts">
import { ref, computed } from 'vue'
import TickerPicker from './TickerPicker.vue'
import type { PickerItem } from './TickerPicker.vue'
import { usePortfolioStore } from '../stores/portfolio'

const store = usePortfolioStore()
const emit = defineEmits<{ submit: [] }>()

const holdings = ref<PickerItem[]>([])
const prices = ref<Record<string, number>>({})
const loadingPrices = ref(false)

const portfolioString = computed(() => {
  if (holdings.value.length === 0) return ''
  const totalValue = holdings.value.reduce((sum, h) => {
    const price = prices.value[h.ticker] || 0
    return sum + h.shares * price
  }, 0)
  if (totalValue === 0) {
    // Fallback: equal-weight if no prices yet
    const w = 1.0 / holdings.value.length
    return holdings.value.map(h => `${h.ticker}:${w.toFixed(4)}`).join(',')
  }
  return holdings.value
    .map(h => {
      const price = prices.value[h.ticker] || 0
      const weight = (h.shares * price) / totalValue
      return `${h.ticker}:${weight.toFixed(4)}`
    })
    .join(',')
})

const holdingSummary = computed(() => {
  if (holdings.value.length === 0) return []
  const totalValue = holdings.value.reduce((sum, h) => {
    const price = prices.value[h.ticker] || 0
    return sum + h.shares * price
  }, 0)
  return holdings.value.map(h => {
    const price = prices.value[h.ticker] || 0
    const value = h.shares * price
    const weight = totalValue > 0 ? (value / totalValue) * 100 : 0
    return { ticker: h.ticker, shares: h.shares, price, value, weight }
  })
})

async function fetchPrices() {
  const tickers = holdings.value.map(h => h.ticker)
  if (tickers.length === 0) return
  loadingPrices.value = true
  try {
    const res = await fetch(`/api/stock/quote?tickers=${tickers.join(',')}`)
    const data: Record<string, number> = await res.json()
    prices.value = { ...prices.value, ...data }
  } catch {
    // Keep existing prices
  }
  loadingPrices.value = false
}

function onHoldingsChange(items: PickerItem[]) {
  holdings.value = items
  // Fetch prices for any new tickers
  const newTickers = items.filter(h => !(h.ticker in prices.value))
  if (newTickers.length > 0) {
    fetchPrices()
  }
}

async function onSubmit() {
  if (holdings.value.length === 0) return
  // Refresh prices before submitting
  await fetchPrices()
  const ps = portfolioString.value
  if (ps) {
    store.portfolio = ps
    emit('submit')
  }
}
</script>

<template>
  <div class="fc-card mb-4">
    <div class="fc-section-header">
      <div class="fc-bar"></div>
      <h2>Portfolio</h2>
    </div>

    <div class="mb-3">
      <label class="text-xs font-semibold opacity-50 uppercase tracking-wider mb-1 block">
        Add Holdings
      </label>
      <TickerPicker :modelValue="holdings" @update:modelValue="onHoldingsChange" />
    </div>

    <!-- Weight summary table -->
    <div v-if="holdingSummary.length > 0" class="mb-3 overflow-x-auto">
      <table class="table table-xs w-full">
        <thead>
          <tr>
            <th>Ticker</th>
            <th class="text-right">Shares</th>
            <th class="text-right">Price</th>
            <th class="text-right">Value</th>
            <th class="text-right">Weight</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in holdingSummary" :key="row.ticker">
            <td class="font-mono font-bold" style="color: oklch(var(--p))">{{ row.ticker }}</td>
            <td class="text-right font-mono">{{ row.shares }}</td>
            <td class="text-right font-mono">{{ row.price > 0 ? `$${row.price.toFixed(2)}` : '—' }}</td>
            <td class="text-right font-mono">{{ row.value > 0 ? `$${row.value.toFixed(0)}` : '—' }}</td>
            <td class="text-right font-mono font-semibold">{{ row.weight.toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
      <p v-if="loadingPrices" class="text-xs opacity-50 mt-1">Fetching prices...</p>
    </div>

    <div class="flex gap-3 items-end">
      <div class="w-20">
        <label class="text-xs font-semibold opacity-50 uppercase tracking-wider mb-1 block">Years</label>
        <input v-model.number="store.years" type="number" min="1" max="20"
               class="input input-bordered w-full text-sm" />
      </div>
      <div class="w-24">
        <label class="text-xs font-semibold opacity-50 uppercase tracking-wider mb-1 block">Benchmark</label>
        <input v-model="store.benchmark" type="text"
               class="input input-bordered w-full text-sm font-mono" />
      </div>
      <button class="btn btn-primary btn-sm" @click="onSubmit"
              :disabled="holdings.length === 0 || loadingPrices">
        Analyze
      </button>
    </div>
  </div>
</template>
