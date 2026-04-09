<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useUniverseStore } from '../stores/universe'

export interface PickerItem {
  ticker: string
  name: string
  shares: number
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

const universeStore = useUniverseStore()
const searchQuery = ref('')
const dropdownOpen = ref(false)
onMounted(() => { universeStore.load() })

const filteredResults = computed(() => {
  const q = searchQuery.value.trim().toUpperCase()
  if (!q || q.length < 1) return []
  const all = universeStore.entries
  const selectedTickers = new Set(props.modelValue.map(s => s.ticker))
  const available = all.filter(u => !selectedTickers.has(u.ticker))

  const tickerMatch = available.filter(u => u.ticker.toUpperCase().startsWith(q))
  const nameMatch = available.filter(u =>
    !u.ticker.toUpperCase().startsWith(q) && u.name.toUpperCase().includes(q)
  )
  return [...tickerMatch, ...nameMatch].slice(0, 50)
})

function selectItem(item: { ticker: string; name: string }) {
  const updated = [...props.modelValue, { ticker: item.ticker, name: item.name, shares: 1 }]
  emit('update:modelValue', updated)
  searchQuery.value = ''
  dropdownOpen.value = false
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
  if (searchQuery.value.trim()) dropdownOpen.value = true
}

function onInputBlur() {
  setTimeout(() => { dropdownOpen.value = false }, 150)
}

watch(searchQuery, (q) => {
  dropdownOpen.value = q.trim().length > 0
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
      <div v-if="dropdownOpen && filteredResults.length > 0" class="fc-picker-dropdown">
        <div v-for="item in filteredResults" :key="item.ticker"
             class="fc-picker-option"
             @mousedown.prevent="selectItem(item)">
          <span class="ticker">{{ item.ticker }}</span>
          <span class="name">{{ item.name }}</span>
        </div>
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
