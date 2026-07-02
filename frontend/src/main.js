import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles.css'
import { currentUser } from './services/api'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
  { path: '/profesor', component: () => import('./views/TeacherDashboard.vue'), meta: { role: 'TEACHER' } },
  { path: '/padres', component: () => import('./views/ParentPortal.vue'), meta: { role: 'PARENT' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    return true
  }

  const user = await currentUser()
  if (!user) {
    return '/login'
  }

  if (to.meta.role && user.role !== to.meta.role) {
    return user.role === 'TEACHER' ? '/profesor' : '/padres'
  }

  return true
})

createApp(App).use(router).mount('#app')
