import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },

  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: 'home', name: 'Home', component: () => import('../views/Home.vue'), meta: { requiresAuth: true } },
      { path: 'profile', name: 'Profile', component: () => import('../views/Profile.vue'), meta: { requiresAuth: true } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('../views/KnowledgeList.vue'), meta: { requiresAuth: true } },
      { path: 'knowledge/:id', name: 'KnowledgeEdit', component: () => import('../views/KnowledgeEdit.vue'), meta: { requiresAuth: true } },
      { path: 'agents', name: 'Agent', component: () => import('../views/Agent.vue'), meta: { requiresAuth: true } },
      { path: 'agents/:id', name: 'AgentDetail', component: () => import('../views/AgentDetail.vue'), meta: { requiresAuth: true } },
      { path: 'assistant', name: 'Assistant', component: () => import('../views/Assistant.vue'), meta: { requiresAuth: true } },
      { path: 'workflows', name: 'Workflow', component: () => import('../views/Workflow.vue'), meta: { requiresAuth: true } },
      { path: 'workflows/:id', name: 'WorkflowDetail', component: () => import('../views/Workflow.vue'), meta: { requiresAuth: true } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
  if (requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/home')
  } else {
    next()
  }
})

export default router
