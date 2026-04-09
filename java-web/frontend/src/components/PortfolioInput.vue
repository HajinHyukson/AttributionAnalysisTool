<script setup lang="ts">
import { usePortfolioStore } from '../stores/portfolio'

const store = usePortfolioStore()
const emit = defineEmits<{ submit: [] }>()

function onSubmit() {
  if (store.portfolio.trim()) {
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
    <div class="flex gap-3 items-end">
      <div class="flex-1">
        <label class="text-xs font-semibold opacity-50 uppercase tracking-wider mb-1 block">
          Holdings (TICKER:WEIGHT)
        </label>
        <textarea
          v-model="store.portfolio"
          placeholder="AAPL:30, MSFT:25, GOOGL:20, JNJ:15, XOM:10"
          class="textarea textarea-bordered w-full text-sm font-mono"
          rows="2"
          @keydown.ctrl.enter="onSubmit"
        />
      </div>
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
      <button class="btn btn-primary btn-sm" @click="onSubmit" :disabled="!store.portfolio.trim()">
        Analyze
      </button>
    </div>
  </div>
</template>
