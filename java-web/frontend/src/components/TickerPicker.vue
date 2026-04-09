<script setup lang="ts">
import { ref, watch } from 'vue'

export interface PickerItem {
  ticker: string
  name: string
  shares: number
}

interface SearchResult {
  ticker: string
  name: string
  exchange: string
}

const props = withDefaults(defineProps<{
  modelValue?: PickerItem[]
  placeholder?: string
}>(), {
  modelValue: () => [],
  placeholder: 'Search ticker or company name...',
})

const emit = defineEmits<{
  'update:modelValue': [items: PickerItem[]]
}>()

const searchQuery = ref('')
const dropdownOpen = ref(false)
const searchResults = ref<SearchResult[]>([])
const searching = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

async function fetchResults(query: string) {
  if (!query || query.length < 1) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    const res = await fetch(`/api/stock/search?q=${encodeURIComponent(query)}&limit=20`)
    const data: SearchResult[] = await res.json()
    const selectedTickers = new Set(props.modelValue.map(s => s.ticker))
    searchResults.value = data.filter(r => !selectedTickers.has(r.ticker))
  } catch {
    searchResults.value = []
  }
  searching.value = false
}

function selectItem(item: SearchResult) {
  const updated = [...props.modelValue, { ticker: item.ticker, name: item.name, shares: 1 }]
  emit('update:modelValue', updated)
  searchQuery.value = ''
  dropdownOpen.value = false
  searchResults.value = []
}

function removeItem(idx: number) {
  const updated = props.modelValue.filter((_, i) => i !== idx)
  emit('update:modelValue', updated)
}

function updateShares(idx: number, shares: number) {
  const updated = [...props.modelValue]
  updated[idx] = { ...updated[idx], shares: Math.max(1, shares) }
  emit('update:modelValue', updated)
}

function onInputFocus() {
  if (searchResults.value.length > 0) dropdownOpen.value = true
}

function onInputBlur() {
  setTimeout(() => { dropdownOpen.value = false }, 150)
}

watch(searchQuery, (q) => {
  const trimmed = q.trim()
  if (debounceTimer) clearTimeout(debounceTimer)
  if (!trimmed) {
    dropdownOpen.value = false
    searchResults.value = []
    return
  }
  debounceTimer = setTimeout(() => {
    fetchResults(trimmed)
    dropdownOpen.value = true
  }, 250)
})
</script>

<template>
  <div>
    <!-- Search input -->
    <div class="relative">
      <input v-model="searchQuery"
             type="text"
             :placeholder="placeholder"
             class="input input-bordered input-sm w-full"
             autocomplete="off"
             @focus="onInputFocus"
             @blur="onInputBlur" />

      <!-- Dropdown -->
      <div v-if="dropdownOpen && searchResults.length > 0" class="fc-picker-dropdown">
        <div v-for="item in searchResults" :key="item.ticker"
             class="fc-picker-option"
             @mousedown.prevent="selectItem(item)">
          <span class="ticker">{{ item.ticker }}</span>
          <span class="name">{{ item.name }}</span>
        </div>
      </div>
      <div v-else-if="dropdownOpen && searching" class="fc-picker-dropdown">
        <div class="fc-picker-option"><span class="name">Searching...</span></div>
      </div>
    </div>

    <!-- Selected chips with shares input -->
    <div v-if="modelValue.length > 0" class="flex flex-wrap gap-2 mt-2">
      <div v-for="(item, idx) in modelValue" :key="item.ticker" class="fc-chip">
        <span class="ticker">{{ item.ticker }}</span>
        <input type="number"
               class="shares-input"
               :value="item.shares"
               min="1"
               @change="updateShares(idx, parseInt(($event.target as HTMLInputElement).value) || 1)" />
        <span class="remove" @click="removeItem(idx)">&#x2715;</span>
      </div>
    </div>
    <p v-else class="text-xs text-base-content/40 mt-2">Search and add stocks to your portfolio.</p>
  </div>
</template>
