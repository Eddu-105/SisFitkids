<script setup>
import { ref } from 'vue'
import { LockKeyhole, UserRound } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import fitKidsLogo from '../assets/fit-kids-logo.png'
import { api } from '../services/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function login() {
  error.value = ''
  loading.value = true
  try {
    const data = await api('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    router.push(data.user.role === 'TEACHER' ? '/profesor' : '/padres')
  } catch (currentError) {
    error.value = currentError.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-screen">
    <section class="login-panel">
      <div class="login-brand">
        <img :src="fitKidsLogo" alt="Fit Kids" />
        <p class="eyebrow">Sistema administrativo</p>
        <h1>SIS Fit Kids</h1>
        <p class="muted">Ingresa con tus credenciales para revisar la informacion de la academia.</p>
      </div>

      <form class="login-form" @submit.prevent="login">
        <label>
          Usuario
          <span class="input-shell">
            <UserRound :size="18" />
            <input v-model="username" autocomplete="username" required type="text" placeholder="profesor o padre" />
          </span>
        </label>
        <label>
          Contrasena
          <span class="input-shell">
            <LockKeyhole :size="18" />
            <input v-model="password" autocomplete="current-password" required type="password" placeholder="********" />
          </span>
        </label>

        <p v-if="error" class="alert error">{{ error }}</p>

        <button class="primary" :disabled="loading" type="submit">
          {{ loading ? 'Ingresando...' : 'Iniciar sesion' }}
        </button>
      </form>

      <div class="login-help">
        <strong>Acceso inicial</strong>
        <span>Padres: usuario DNI y contrasena P + DNI. Ejemplo: 12345678 / P12345678</span>
      </div>
    </section>
  </main>
</template>
