import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/overview' },
  { path: '/overview', component: () => import('./views/DashboardHome.vue') },
  { path: '/risk', component: () => import('./views/RiskAttribution.vue') },
  { path: '/performance', component: () => import('./views/PerformanceAttribution.vue') },
  { path: '/stress', component: () => import('./views/StressTesting.vue') },
  { path: '/correlation', component: () => import('./views/CorrelationRegime.vue') },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})
