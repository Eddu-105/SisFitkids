<script setup>
import { computed, onMounted, ref } from 'vue'
import { CalendarDays, CreditCard, LineChart, MessageCircle, UserRound } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const parent = ref(null)
const children = ref([])
const payments = ref([])
const attendance = ref([])
const progress = ref([])
const announcements = ref([])
const selectedChildId = ref('')
const savingProfile = ref(false)
const success = ref('')
const profileForm = ref({
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  address: '',
  emergency_phone: '',
})
const dayOptions = [
  { value: 1, label: 'Lunes' },
  { value: 2, label: 'Martes' },
  { value: 3, label: 'Miercoles' },
  { value: 4, label: 'Jueves' },
  { value: 5, label: 'Viernes' },
  { value: 6, label: 'Sabado' },
  { value: 7, label: 'Domingo' },
]

const child = computed(() => children.value.find((currentChild) => String(currentChild.id) === String(selectedChildId.value)) || children.value[0] || null)
const childPayments = computed(() => payments.value.filter((payment) => payment.student.id === child.value?.id))
const childAttendance = computed(() => attendance.value.filter((record) => record.student.id === child.value?.id))
const childProgress = computed(() => progress.value.filter((item) => item.student.id === child.value?.id))
const pendingPayment = computed(() => childPayments.value.find((payment) => payment.status !== 'PAID'))
const pendingPaymentsCount = computed(() => childPayments.value.filter((payment) => payment.status !== 'PAID').length)
const childSchedule = computed(() => {
  const group = child.value?.class_group
  if (!group) {
    return []
  }
  const days = group.days_of_week?.length ? group.days_of_week.map(Number) : [Number(group.day_of_week)].filter(Boolean)
  return dayOptions.map((day) => ({
    ...day,
    group: days.includes(day.value) ? group : null,
  }))
})

function groupDayText(group) {
  return group?.day_labels?.length ? group.day_labels.join(', ') : group?.day_label
}

function syncProfileForm(currentParent) {
  profileForm.value = {
    first_name: currentParent?.first_name || '',
    last_name: currentParent?.last_name || '',
    phone: currentParent?.phone || '',
    email: currentParent?.email || '',
    address: currentParent?.address || '',
    emergency_phone: currentParent?.emergency_phone || '',
  }
}

async function loadPortal() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const data = await api('/api/parent-portal/')
    parent.value = data.parent
    syncProfileForm(data.parent)
    children.value = data.children
    payments.value = data.payments
    attendance.value = data.attendance
    progress.value = data.progress
    announcements.value = data.announcements
    selectedChildId.value = data.children[0]?.id || ''
  } catch (currentError) {
    error.value = currentError.message
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  error.value = ''
  success.value = ''
  savingProfile.value = true
  try {
    const updatedParent = await api('/api/parent-portal/', {
      method: 'PATCH',
      body: JSON.stringify(profileForm.value),
    })
    parent.value = updatedParent
    syncProfileForm(updatedParent)
    success.value = 'Datos actualizados correctamente.'
  } catch (currentError) {
    error.value = currentError.message
  } finally {
    savingProfile.value = false
  }
}

async function logout() {
  await api('/api/auth/logout/', { method: 'POST', body: JSON.stringify({}) })
  router.push('/login')
}

onMounted(loadPortal)
</script>

<template>
  <main class="parent-shell">
    <header class="parent-header">
      <div>
        <p class="eyebrow">Portal de padres</p>
        <h1>Hola, {{ parent?.full_name || 'familia' }}</h1>
      </div>
      <button class="secondary link-button" type="button" @click="logout">Salir</button>
    </header>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="success" class="alert success">{{ success }}</p>
    <p v-if="loading" class="empty-state">Cargando informacion...</p>

    <section v-if="children.length > 1" class="child-tabs" aria-label="Hijos">
      <button
        v-for="currentChild in children"
        :key="currentChild.id"
        :class="{ active: currentChild.id === child?.id }"
        type="button"
        @click="selectedChildId = currentChild.id"
      >
        {{ currentChild.full_name }}
      </button>
    </section>

    <section v-if="child" class="parent-grid">
      <article class="profile-panel">
        <UserRound :size="34" />
        <div>
          <span>Alumno</span>
          <strong>{{ child.full_name }}</strong>
          <small>Estado {{ child.status_label }}</small>
        </div>
      </article>

      <article class="parent-card">
        <CalendarDays :size="24" />
        <span>Horario</span>
        <strong>{{ child.class_group ? `${groupDayText(child.class_group)} ${child.class_group.start_time}` : 'Sin grupo' }}</strong>
      </article>
      <article class="parent-card">
        <CreditCard :size="24" />
        <span>Mensualidad</span>
        <strong>{{ pendingPayment ? pendingPayment.status_label : 'Sin deuda' }}</strong>
      </article>
      <article class="parent-card">
        <LineChart :size="24" />
        <span>Pagos pendientes</span>
        <strong>{{ pendingPaymentsCount }}</strong>
      </article>
    </section>

    <p v-if="!child && !loading" class="empty-state">Todavia no hay alumnos asociados a tu usuario.</p>

    <section v-if="parent" class="panel profile-edit-panel">
      <div class="panel-header">
        <h2>Mis datos</h2>
      </div>
      <form class="data-form" @submit.prevent="saveProfile">
        <div class="form-grid">
          <label>
            Nombres
            <input v-model="profileForm.first_name" required type="text" />
          </label>
          <label>
            Apellidos
            <input v-model="profileForm.last_name" required type="text" />
          </label>
        </div>
        <div class="form-grid">
          <label>
            Telefono
            <input v-model="profileForm.phone" required type="tel" />
          </label>
          <label>
            Correo
            <input v-model="profileForm.email" type="email" />
          </label>
        </div>
        <label>
          Direccion
          <input v-model="profileForm.address" type="text" />
        </label>
        <label>
          Telefono de emergencia
          <input v-model="profileForm.emergency_phone" type="tel" />
        </label>
        <div class="form-actions">
          <button class="primary" :disabled="savingProfile" type="submit">
            {{ savingProfile ? 'Guardando...' : 'Guardar datos' }}
          </button>
        </div>
      </form>
    </section>

    <section v-if="child" class="content-grid">
      <article class="panel wide">
        <div class="panel-header">
          <h2>Resumen del alumno</h2>
        </div>
        <div class="timeline">
          <div>
            <span>Grupo</span>
            <strong>
              {{ child.class_group ? `${child.class_group.name}, ${groupDayText(child.class_group)} ${child.class_group.start_time} - ${child.class_group.end_time}` : 'Sin grupo asignado' }}
            </strong>
          </div>
          <div>
            <span>Notas medicas</span>
            <strong>{{ child.medical_notes || 'Sin notas registradas' }}</strong>
          </div>
          <div>
            <span>Observaciones</span>
            <strong>{{ child.teacher_notes || 'Sin observaciones registradas' }}</strong>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-header">
          <h2><CalendarDays :size="19" /> Calendario</h2>
        </div>
        <section class="mini-week-calendar">
          <article v-for="day in childSchedule" :key="day.value" class="mini-calendar-day">
            <span>{{ day.label }}</span>
            <strong v-if="day.group" :style="{ borderColor: day.group.color }">
              {{ day.group.start_time }} - {{ day.group.end_time }}
            </strong>
            <small v-else>Libre</small>
          </article>
        </section>
      </article>
    </section>

    <section v-if="child" class="content-grid">
      <article class="panel">
        <div class="panel-header">
          <h2><MessageCircle :size="19" /> Pagos</h2>
        </div>
        <ul class="notice-list">
          <li v-for="payment in childPayments" :key="payment.id">
            {{ payment.concept }} - S/ {{ payment.amount }} - {{ payment.status_label }}
          </li>
          <li v-if="!childPayments.length">No hay pagos registrados para este alumno.</li>
        </ul>
      </article>
      <article class="panel wide">
        <div class="panel-header">
          <h2>Progreso</h2>
        </div>
        <div class="timeline">
          <div v-for="item in childProgress" :key="item.id">
            <span>{{ item.date }}</span>
            <strong>Peso {{ item.weight_kg || '-' }} kg, talla {{ item.height_cm || '-' }} cm, fuerza {{ item.strength }}, resistencia {{ item.endurance }}</strong>
            <small>{{ item.notes || 'Sin observaciones' }}</small>
          </div>
          <div v-if="!childProgress.length">
            <span>Sin evaluaciones</span>
            <strong>Aun no hay progreso registrado.</strong>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-header">
          <h2>Asistencia</h2>
        </div>
        <ul class="notice-list">
          <li v-for="record in childAttendance" :key="record.id">
            {{ record.session.date }} - {{ record.session.class_group.name }} - {{ record.status_label }}
          </li>
          <li v-if="!childAttendance.length">No hay asistencias registradas.</li>
        </ul>
      </article>
    </section>

    <section class="panel notices-panel">
      <div class="panel-header">
        <h2><MessageCircle :size="19" /> Avisos</h2>
      </div>
      <ul class="notice-list inline">
        <li v-for="notice in announcements" :key="notice.id">
          <strong>{{ notice.title }}</strong><br />
          {{ notice.body }}
        </li>
        <li v-if="!announcements.length">No hay comunicados activos.</li>
      </ul>
    </section>
  </main>
</template>
