import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface UniverseEntry {
  ticker: string
  name: string
}

export const useUniverseStore = defineStore('universe', () => {
  const entries = ref<UniverseEntry[]>([])
  const loaded = ref(false)
  const loading = ref(false)

  async function load() {
    if (loaded.value || loading.value) return
    loading.value = true
    try {
      const res = await fetch('/api/portfolio/universe')
      const data = await res.json()
      entries.value = data.map(([ticker, name]: [string, string]) => ({ ticker, name }))
      loaded.value = true
    } catch (e) {
      console.error('Failed to load universe', e)
    }
    loading.value = false
  }

  return { entries, loaded, loading, load }
})
