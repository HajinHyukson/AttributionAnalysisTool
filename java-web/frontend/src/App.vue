<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref } from 'vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

const navItems = [
  { path: '/overview', icon: '📊', label: 'Overview' },
  { path: '/risk', icon: '⚡', label: 'Risk Attribution' },
  { path: '/performance', icon: '📈', label: 'Performance' },
  { path: '/stress', icon: '🔥', label: 'Stress Test' },
  { path: '/correlation', icon: '🔗', label: 'Correlations' },
]
</script>

<template>
  <div class="min-h-screen flex fc-bg-grid" data-theme="faustcalc">
    <aside :class="['fc-sidebar flex-shrink-0 flex flex-col transition-all', sidebarCollapsed ? 'w-14' : 'w-52']">
      <div class="p-3 border-b border-white/8">
        <div class="flex items-center gap-2" :class="{ 'justify-center': sidebarCollapsed }">
          <span class="fc-brand-mark">A</span>
          <div v-if="!sidebarCollapsed" class="flex flex-col leading-tight">
            <span class="fc-brand-title">FaustCalc</span>
            <span class="fc-brand-subtitle">Attribution Analysis</span>
          </div>
        </div>
      </div>

      <nav class="flex-1 p-2 space-y-0.5 overflow-y-auto">
        <div class="fc-nav-label" v-if="!sidebarCollapsed">Analytics</div>
        <router-link v-for="item in navItems" :key="item.path"
                     :to="item.path"
                     :class="['fc-nav-item', route.path === item.path ? 'active' : '']">
          <span>{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="p-2 border-t border-white/8">
        <button class="fc-nav-item justify-center" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '→' : '←' }}
        </button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto min-h-screen">
      <div class="max-w-6xl mx-auto px-5 py-6">
        <router-view />
      </div>
    </main>
  </div>
</template>
