<script setup>
import { computed, onMounted, ref } from 'vue'
import { CalendarDays, CreditCard, MessageSquareText, Plus, RefreshCcw, Search, UsersRound } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const router = useRouter()
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''
const exportReportUrl = `${apiBaseUrl}/api/reports/export/`
const activeTab = ref('students')
const activeMode = ref('list')
const loading = ref(false)
const error = ref('')
const success = ref('')
const summary = ref({ students: 0, parents: 0, pending_payments: 0, weekly_classes: 0 })
const parents = ref([])
const students = ref([])
const classGroups = ref([])
const payments = ref([])
const attendanceSessions = ref([])
const progressItems = ref([])
const announcements = ref([])
const reports = ref(null)
const settings = ref({ academy_name: 'SIS Fit Kids', teacher_name: '', phone: '', address: '', default_monthly_fee: '0.00' })
const editing = ref({ type: '', id: null })
const confirmModal = ref({ open: false, type: '', id: null, label: '' })
const filters = ref({
  students: '',
  parents: '',
  groups: '',
  payments: '',
  studentGroup: '',
  groupDay: '',
  paymentStatus: '',
})

const attendanceForm = ref({ class_group_id: '', date: new Date().toISOString().slice(0, 10), notes: '' })
const progressForm = ref({
  student_id: '',
  date: new Date().toISOString().slice(0, 10),
  weight_kg: '',
  height_cm: '',
  strength: 0,
  endurance: 0,
  coordination: 0,
  flexibility: 0,
  notes: '',
})
const announcementForm = ref({ title: '', body: '', parent_id: '', is_active: true })

const dayOptions = [
  { value: 1, label: 'Lunes' },
  { value: 2, label: 'Martes' },
  { value: 3, label: 'Miercoles' },
  { value: 4, label: 'Jueves' },
  { value: 5, label: 'Viernes' },
  { value: 6, label: 'Sabado' },
  { value: 7, label: 'Domingo' },
]

const groupColors = ['#0d7467', '#1d4ed8', '#be123c', '#7c3aed', '#b45309', '#047857', '#c2410c', '#0369a1']

const parentForm = ref({
  first_name: '',
  last_name: '',
  dni: '',
  phone: '',
  email: '',
  address: '',
  emergency_phone: '',
})

const studentForm = ref({
  parent_id: '',
  class_group_id: '',
  first_name: '',
  last_name: '',
  birth_date: '',
  weight_kg: '',
  height_cm: '',
  medical_notes: '',
  teacher_notes: '',
})

const groupForm = ref({
  name: '',
  day_of_week: '',
  days_of_week: [],
  start_time: '',
  end_time: '',
  capacity: 12,
  age_range: '',
  color: groupColors[0],
})

const paymentForm = ref({
  student_id: '',
  concept: 'Mensualidad',
  amount: '',
  due_date: '',
  paid_date: '',
  status: 'PENDING',
  notes: '',
})

const activeStudents = computed(() => students.value.filter((student) => student.status === 'ACTIVE').length)
const isEditingCurrentTab = computed(() => editing.value.type === activeTab.value && editing.value.id !== null)
const crudTabs = ['students', 'parents', 'groups', 'payments']
const isCrudTab = computed(() => crudTabs.includes(activeTab.value))
const filteredStudents = computed(() => {
  const search = filters.value.students.trim().toLowerCase()
  return students.value.filter((student) => {
    const matchesSearch = !search || [
      student.full_name,
      student.parent.full_name,
      student.class_group?.name || '',
    ].some((value) => value.toLowerCase().includes(search))
    const matchesGroup = !filters.value.studentGroup || String(student.class_group?.id || '') === String(filters.value.studentGroup)
    return matchesSearch && matchesGroup
  })
})
const filteredParents = computed(() => {
  const search = filters.value.parents.trim().toLowerCase()
  return parents.value.filter((parent) => !search || [
    parent.full_name,
    parent.dni,
    parent.phone,
    parent.email,
  ].some((value) => (value || '').toLowerCase().includes(search)))
})
const filteredGroups = computed(() => {
  const search = filters.value.groups.trim().toLowerCase()
  return classGroups.value.filter((group) => {
    const matchesSearch = !search || [group.name, group.age_range, groupDayText(group)].some((value) => (value || '').toLowerCase().includes(search))
    const matchesDay = !filters.value.groupDay || groupDays(group).some((day) => String(day) === String(filters.value.groupDay))
    return matchesSearch && matchesDay
  })
})
const weeklyCalendar = computed(() => dayOptions.map((day) => ({
  ...day,
  groups: classGroups.value
    .filter((group) => group.is_active && groupDays(group).includes(day.value))
    .sort((first, second) => first.start_time.localeCompare(second.start_time)),
})))
const filteredPayments = computed(() => {
  const search = filters.value.payments.trim().toLowerCase()
  return payments.value.filter((payment) => {
    const matchesSearch = !search || [
      payment.student.full_name,
      payment.concept,
      payment.student.parent.full_name,
    ].some((value) => value.toLowerCase().includes(search))
    const matchesStatus = !filters.value.paymentStatus || payment.status === filters.value.paymentStatus
    return matchesSearch && matchesStatus
  })
})

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function groupDays(group) {
  return group.days_of_week?.length ? group.days_of_week.map(Number) : [Number(group.day_of_week)].filter(Boolean)
}

function groupDayText(group) {
  return group.day_labels?.length ? group.day_labels.join(', ') : group.day_label
}

function toggleGroupDay(dayValue) {
  const currentDays = new Set(groupForm.value.days_of_week.map(Number))
  if (currentDays.has(dayValue)) {
    currentDays.delete(dayValue)
  } else {
    currentDays.add(dayValue)
  }
  const selectedDays = [...currentDays].sort((first, second) => first - second)
  groupForm.value.days_of_week = selectedDays
  groupForm.value.day_of_week = selectedDays[0] || ''
}

function switchModule(module) {
  activeTab.value = module
  activeMode.value = 'list'
  cancelEdit()
}

function openForm(module = activeTab.value) {
  activeTab.value = module
  activeMode.value = 'form'
}

function startCreate(module = activeTab.value) {
  activeTab.value = module
  resetEditing()
  resetParentForm()
  resetStudentForm()
  resetGroupForm()
  resetPaymentForm()
  activeMode.value = 'form'
}

function resetEditing() {
  editing.value = { type: '', id: null }
}

function resetParentForm() {
  parentForm.value = {
    first_name: '',
    last_name: '',
    dni: '',
    phone: '',
    email: '',
    address: '',
    emergency_phone: '',
  }
}

function resetStudentForm() {
  studentForm.value = {
    parent_id: '',
    class_group_id: '',
    first_name: '',
    last_name: '',
    birth_date: '',
    weight_kg: '',
    height_cm: '',
    medical_notes: '',
    teacher_notes: '',
  }
}

function resetGroupForm() {
  groupForm.value = {
    name: '',
    day_of_week: '',
    days_of_week: [],
    start_time: '',
    end_time: '',
    capacity: 12,
    age_range: '',
    color: groupColors[0],
  }
}

function resetPaymentForm() {
  paymentForm.value = {
    student_id: '',
    concept: 'Mensualidad',
    amount: '',
    due_date: '',
    paid_date: '',
    status: 'PENDING',
    notes: '',
  }
}

function cancelEdit() {
  resetEditing()
  resetParentForm()
  resetStudentForm()
  resetGroupForm()
  resetPaymentForm()
  activeMode.value = 'list'
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [summaryData, parentsData, studentsData, groupsData, paymentsData] = await Promise.all([
      api('/api/dashboard/summary/'),
      api('/api/parents/'),
      api('/api/students/'),
      api('/api/class-groups/'),
      api('/api/payments/'),
    ])
    summary.value = summaryData
    parents.value = parentsData.results
    students.value = studentsData.results
    classGroups.value = groupsData.results
    payments.value = paymentsData.results
    const [attendanceData, progressData, announcementData, reportData, settingsData] = await Promise.all([
      api('/api/attendance-sessions/'),
      api('/api/progress/'),
      api('/api/announcements/'),
      api('/api/reports/summary/'),
      api('/api/settings/'),
    ])
    attendanceSessions.value = attendanceData.results
    progressItems.value = progressData.results
    announcements.value = announcementData.results
    reports.value = reportData
    settings.value = settingsData
  } catch (currentError) {
    error.value = currentError.message
  } finally {
    loading.value = false
  }
}

async function createAttendanceSession() {
  error.value = ''
  success.value = ''
  try {
    const session = await api('/api/attendance-sessions/', {
      method: 'POST',
      body: JSON.stringify(attendanceForm.value),
    })
    attendanceSessions.value = [session, ...attendanceSessions.value.filter((item) => item.id !== session.id)]
    success.value = 'Sesion de asistencia creada.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function updateAttendance(record, status) {
  error.value = ''
  success.value = ''
  try {
    await api(`/api/attendance-records/${record.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    await loadData()
    success.value = 'Asistencia actualizada.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function createProgress() {
  error.value = ''
  success.value = ''
  try {
    const item = await api('/api/progress/', {
      method: 'POST',
      body: JSON.stringify(progressForm.value),
    })
    progressItems.value = [item, ...progressItems.value]
    progressForm.value = { student_id: '', date: todayIso(), weight_kg: '', height_cm: '', strength: 0, endurance: 0, coordination: 0, flexibility: 0, notes: '' }
    success.value = 'Evaluacion registrada.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function createAnnouncement() {
  error.value = ''
  success.value = ''
  try {
    const item = await api('/api/announcements/', {
      method: 'POST',
      body: JSON.stringify(announcementForm.value),
    })
    announcements.value = [item, ...announcements.value]
    announcementForm.value = { title: '', body: '', parent_id: '', is_active: true }
    success.value = 'Comunicado publicado.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function saveSettings() {
  error.value = ''
  success.value = ''
  try {
    settings.value = await api('/api/settings/', {
      method: 'PUT',
      body: JSON.stringify(settings.value),
    })
    success.value = 'Configuracion guardada.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function createParent() {
  error.value = ''
  success.value = ''
  const wasEditing = editing.value.type === 'parents'
  try {
    const parent = await api(wasEditing ? `/api/parents/${editing.value.id}/` : '/api/parents/', {
      method: wasEditing ? 'PUT' : 'POST',
      body: JSON.stringify(parentForm.value),
    })
    if (wasEditing) {
      parents.value = parents.value.map((currentParent) => currentParent.id === parent.id ? parent : currentParent)
    } else {
      parents.value = [parent, ...parents.value]
      summary.value.parents += 1
    }
    resetParentForm()
    resetEditing()
    activeMode.value = 'list'
    success.value = wasEditing ? 'Padre actualizado correctamente.' : 'Padre registrado correctamente.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function createStudent() {
  error.value = ''
  success.value = ''
  const wasEditing = editing.value.type === 'students'
  try {
    const student = await api(wasEditing ? `/api/students/${editing.value.id}/` : '/api/students/', {
      method: wasEditing ? 'PUT' : 'POST',
      body: JSON.stringify(studentForm.value),
    })
    if (wasEditing) {
      students.value = students.value.map((currentStudent) => currentStudent.id === student.id ? student : currentStudent)
    } else {
      students.value = [student, ...students.value]
      summary.value.students += 1
    }
    resetStudentForm()
    resetEditing()
    activeMode.value = 'list'
    success.value = wasEditing ? 'Alumno actualizado correctamente.' : 'Alumno registrado correctamente.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function createGroup() {
  error.value = ''
  success.value = ''
  const wasEditing = editing.value.type === 'groups'
  if (!groupForm.value.days_of_week.length) {
    error.value = 'Selecciona al menos un dia para el horario.'
    return
  }
  try {
    const group = await api(wasEditing ? `/api/class-groups/${editing.value.id}/` : '/api/class-groups/', {
      method: wasEditing ? 'PUT' : 'POST',
      body: JSON.stringify(groupForm.value),
    })
    if (wasEditing) {
      classGroups.value = classGroups.value.map((currentGroup) => currentGroup.id === group.id ? group : currentGroup)
    } else {
      classGroups.value = [group, ...classGroups.value]
      summary.value.weekly_classes += 1
    }
    resetGroupForm()
    resetEditing()
    activeMode.value = 'list'
    success.value = wasEditing ? 'Horario actualizado correctamente.' : 'Horario registrado correctamente.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function createPayment() {
  error.value = ''
  success.value = ''
  const wasEditing = editing.value.type === 'payments'
  try {
    const payment = await api(wasEditing ? `/api/payments/${editing.value.id}/` : '/api/payments/', {
      method: wasEditing ? 'PUT' : 'POST',
      body: JSON.stringify(paymentForm.value),
    })
    if (wasEditing) {
      payments.value = payments.value.map((currentPayment) => currentPayment.id === payment.id ? payment : currentPayment)
    } else {
      payments.value = [payment, ...payments.value]
    }
    if (!wasEditing && payment.status !== 'PAID') {
      summary.value.pending_payments += 1
    }
    resetPaymentForm()
    resetEditing()
    activeMode.value = 'list'
    success.value = wasEditing ? 'Pago actualizado correctamente.' : 'Pago registrado correctamente.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

function editParent(parent) {
  activeTab.value = 'parents'
  activeMode.value = 'form'
  editing.value = { type: 'parents', id: parent.id }
  parentForm.value = {
    first_name: parent.first_name,
    last_name: parent.last_name,
    dni: parent.dni,
    phone: parent.phone,
    email: parent.email,
    address: parent.address,
    emergency_phone: parent.emergency_phone,
  }
}

function editStudent(student) {
  activeTab.value = 'students'
  activeMode.value = 'form'
  editing.value = { type: 'students', id: student.id }
  studentForm.value = {
    parent_id: student.parent.id,
    class_group_id: student.class_group?.id || '',
    first_name: student.first_name,
    last_name: student.last_name,
    birth_date: student.birth_date,
    weight_kg: student.weight_kg,
    height_cm: student.height_cm,
    medical_notes: student.medical_notes,
    teacher_notes: student.teacher_notes,
  }
}

function editGroup(group) {
  activeTab.value = 'groups'
  activeMode.value = 'form'
  editing.value = { type: 'groups', id: group.id }
  groupForm.value = {
    name: group.name,
    day_of_week: group.day_of_week,
    days_of_week: groupDays(group),
    start_time: group.start_time,
    end_time: group.end_time,
    capacity: group.capacity,
    age_range: group.age_range,
    color: group.color || groupColors[0],
  }
}

function editPayment(payment) {
  activeTab.value = 'payments'
  activeMode.value = 'form'
  editing.value = { type: 'payments', id: payment.id }
  paymentForm.value = {
    student_id: payment.student.id,
    concept: payment.concept,
    amount: payment.amount,
    due_date: payment.due_date,
    paid_date: payment.paid_date,
    status: payment.status,
    notes: payment.notes,
  }
}

async function deleteItem(type, id) {
  const labels = {
    parents: 'este padre',
    students: 'este alumno',
    groups: 'este horario',
    payments: 'este pago',
  }
  confirmModal.value = { open: true, type, id, label: labels[type] }
}

async function confirmDelete() {
  error.value = ''
  success.value = ''
  const paths = {
    parents: `/api/parents/${confirmModal.value.id}/`,
    students: `/api/students/${confirmModal.value.id}/`,
    groups: `/api/class-groups/${confirmModal.value.id}/`,
    payments: `/api/payments/${confirmModal.value.id}/`,
  }

  try {
    await api(paths[confirmModal.value.type], { method: 'DELETE' })
    await loadData()
    cancelEdit()
    confirmModal.value = { open: false, type: '', id: null, label: '' }
    success.value = 'Registro eliminado correctamente.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

function closeConfirm() {
  confirmModal.value = { open: false, type: '', id: null, label: '' }
}

async function updatePaymentStatus(payment, status) {
  error.value = ''
  success.value = ''
  try {
    const updated = await api(`/api/payments/${payment.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({
        status,
        paid_date: status === 'PAID' ? (payment.paid_date || todayIso()) : '',
      }),
    })
    payments.value = payments.value.map((currentPayment) => currentPayment.id === updated.id ? updated : currentPayment)
    await loadData()
    success.value = 'Estado de pago actualizado.'
  } catch (currentError) {
    error.value = currentError.message
  }
}

async function logout() {
  await api('/api/auth/logout/', { method: 'POST', body: JSON.stringify({}) })
  router.push('/login')
}

onMounted(loadData)
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">SF</span>
        <div>
          <strong>SIS Fit Kids</strong>
          <small>Profesor</small>
        </div>
      </div>
      <nav>
        <a :class="{ active: activeTab === 'students' }" @click="switchModule('students')"><UsersRound :size="18" /> Alumnos</a>
        <a :class="{ active: activeTab === 'parents' }" @click="switchModule('parents')"><UsersRound :size="18" /> Padres</a>
        <a :class="{ active: activeTab === 'groups' }" @click="switchModule('groups')"><CalendarDays :size="18" /> Horarios</a>
        <a :class="{ active: activeTab === 'payments' }" @click="switchModule('payments')"><CreditCard :size="18" /> Pagos</a>
        <a :class="{ active: activeTab === 'attendance' }" @click="switchModule('attendance')"><CalendarDays :size="18" /> Asistencia</a>
        <a :class="{ active: activeTab === 'progress' }" @click="switchModule('progress')"><UsersRound :size="18" /> Progreso</a>
        <a :class="{ active: activeTab === 'announcements' }" @click="switchModule('announcements')"><MessageSquareText :size="18" /> Comunicados</a>
        <a :class="{ active: activeTab === 'reports' }" @click="switchModule('reports')"><CreditCard :size="18" /> Reportes</a>
        <a :class="{ active: activeTab === 'settings' }" @click="switchModule('settings')"><MessageSquareText :size="18" /> Configuracion</a>
      </nav>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Panel administrativo</p>
          <h1>Resumen del profesor</h1>
        </div>
        <div class="toolbar-actions">
          <button class="secondary compact" type="button" @click="loadData"><RefreshCcw :size="18" /> Actualizar</button>
          <button class="secondary compact" type="button" @click="logout">Salir</button>
          <button class="primary compact" type="button" @click="startCreate('students')"><Plus :size="18" /> Nuevo alumno</button>
        </div>
      </header>

      <p v-if="error" class="alert error">{{ error }}</p>
      <p v-if="success" class="alert success">{{ success }}</p>

      <section class="metrics-grid">
        <article class="metric">
          <span>Alumnos activos</span>
          <strong>{{ activeStudents }}</strong>
        </article>
        <article class="metric">
          <span>Padres registrados</span>
          <strong>{{ summary.parents }}</strong>
        </article>
        <article class="metric">
          <span>Clases esta semana</span>
          <strong>{{ summary.weekly_classes }}</strong>
        </article>
        <article class="metric">
          <span>Pagos pendientes</span>
          <strong>{{ summary.pending_payments }}</strong>
        </article>
      </section>

      <section class="tabbar" aria-label="Modulos principales">
        <button :class="{ active: activeTab === 'students' }" type="button" @click="switchModule('students')">Alumnos</button>
        <button :class="{ active: activeTab === 'parents' }" type="button" @click="switchModule('parents')">Padres</button>
        <button :class="{ active: activeTab === 'groups' }" type="button" @click="switchModule('groups')">Horarios</button>
        <button :class="{ active: activeTab === 'payments' }" type="button" @click="switchModule('payments')">Pagos</button>
        <button :class="{ active: activeTab === 'attendance' }" type="button" @click="switchModule('attendance')">Asistencia</button>
        <button :class="{ active: activeTab === 'progress' }" type="button" @click="switchModule('progress')">Progreso</button>
        <button :class="{ active: activeTab === 'announcements' }" type="button" @click="switchModule('announcements')">Comunicados</button>
        <button :class="{ active: activeTab === 'reports' }" type="button" @click="switchModule('reports')">Reportes</button>
        <button :class="{ active: activeTab === 'settings' }" type="button" @click="switchModule('settings')">Configuracion</button>
      </section>

      <section v-if="isCrudTab" class="subtabbar" aria-label="Acciones del modulo">
        <button :class="{ active: activeMode === 'list' }" type="button" @click="cancelEdit">Listado</button>
        <button
          :class="{ active: activeMode === 'form' }"
          type="button"
          @click="isEditingCurrentTab ? openForm(activeTab) : startCreate(activeTab)"
        >
          {{
            activeTab === 'students'
              ? 'Formulario de alumno'
              : activeTab === 'parents'
                ? 'Formulario de padre'
                : activeTab === 'groups'
                  ? 'Formulario de horario'
                  : 'Formulario de pago'
          }}
        </button>
      </section>

      <section class="module-grid">
        <article v-if="activeTab === 'students' && activeMode === 'list'" class="panel wide">
          <div class="panel-header">
            <h2>Alumnos registrados</h2>
            <div class="filter-bar">
              <label class="search-box"><Search :size="17" /><input v-model="filters.students" type="search" placeholder="Buscar alumno o padre" /></label>
              <select v-model="filters.studentGroup" class="filter-select">
                <option value="">Todos los grupos</option>
                <option v-for="group in classGroups" :key="group.id" :value="group.id">{{ group.name }}</option>
              </select>
            </div>
          </div>
          <div class="table">
            <div class="table-row table-head">
              <span>Alumno</span>
              <span>Padre</span>
              <span>Nacimiento</span>
              <span>Acciones</span>
            </div>
            <div v-for="student in filteredStudents" :key="student.id" class="table-row">
              <span><strong>{{ student.full_name }}</strong><small>{{ student.class_group?.name || 'Sin grupo asignado' }}</small></span>
              <span>{{ student.parent.full_name }}</span>
              <span>{{ student.birth_date }} <mark class="ok">{{ student.status_label }}</mark></span>
              <span class="row-actions">
                <button class="ghost-button" type="button" @click="editStudent(student)">Editar</button>
                <button class="danger-button" type="button" @click="deleteItem('students', student.id)">Eliminar</button>
              </span>
            </div>
            <p v-if="!filteredStudents.length && !loading" class="empty-state">No hay alumnos para los filtros actuales.</p>
          </div>
        </article>

        <article v-if="activeTab === 'parents' && activeMode === 'list'" class="panel wide">
          <div class="panel-header">
            <h2>Padres registrados</h2>
            <div class="filter-bar">
              <label class="search-box"><Search :size="17" /><input v-model="filters.parents" type="search" placeholder="Buscar padre, DNI o telefono" /></label>
            </div>
          </div>
          <div class="table parents-table">
            <div class="table-row table-head">
              <span>Padre</span>
              <span>Contacto</span>
              <span>DNI</span>
              <span>Acciones</span>
            </div>
            <div v-for="parent in filteredParents" :key="parent.id" class="table-row">
              <span><strong>{{ parent.full_name }}</strong><small>{{ parent.email || 'Sin correo' }}</small></span>
              <span>{{ parent.phone }}</span>
              <span>{{ parent.dni || '-' }} <mark class="ok">{{ parent.children_count }} hijos</mark></span>
              <span class="row-actions">
                <button class="ghost-button" type="button" @click="editParent(parent)">Editar</button>
                <button class="danger-button" type="button" @click="deleteItem('parents', parent.id)">Eliminar</button>
              </span>
            </div>
            <p v-if="!filteredParents.length && !loading" class="empty-state">No hay padres para los filtros actuales.</p>
          </div>
        </article>

        <article v-if="activeTab === 'groups' && activeMode === 'list'" class="panel wide">
          <div class="panel-header">
            <h2>Horarios registrados</h2>
            <div class="filter-bar">
              <label class="search-box"><Search :size="17" /><input v-model="filters.groups" type="search" placeholder="Buscar grupo" /></label>
              <select v-model="filters.groupDay" class="filter-select">
                <option value="">Todos los dias</option>
                <option v-for="day in dayOptions" :key="day.value" :value="day.value">{{ day.label }}</option>
              </select>
            </div>
          </div>
          <div class="table">
            <div class="table-row table-head">
              <span>Grupo</span>
              <span>Dias</span>
              <span>Horario</span>
              <span>Acciones</span>
            </div>
            <div v-for="group in filteredGroups" :key="group.id" class="table-row">
              <span><strong><i class="color-dot" :style="{ background: group.color }"></i>{{ group.name }}</strong><small>{{ group.age_range || 'Sin rango definido' }}</small></span>
              <span>{{ groupDayText(group) }}</span>
              <span>{{ group.start_time }} - {{ group.end_time }} <mark class="ok">{{ group.students_count }}/{{ group.capacity }}</mark></span>
              <span class="row-actions">
                <button class="ghost-button" type="button" @click="editGroup(group)">Editar</button>
                <button class="danger-button" type="button" @click="deleteItem('groups', group.id)">Eliminar</button>
              </span>
            </div>
            <p v-if="!filteredGroups.length && !loading" class="empty-state">No hay horarios para los filtros actuales.</p>
          </div>
          <section class="week-calendar">
            <article v-for="day in weeklyCalendar" :key="day.value" class="calendar-day">
              <h3>{{ day.label }}</h3>
              <div v-for="group in day.groups" :key="`${day.value}-${group.id}`" class="calendar-event" :style="{ borderColor: group.color }">
                <span class="calendar-time">{{ group.start_time }} - {{ group.end_time }}</span>
                <strong>{{ group.name }}</strong>
                <small>{{ group.students_count }}/{{ group.capacity }} cupos</small>
              </div>
              <p v-if="!day.groups.length" class="calendar-empty">Libre</p>
            </article>
          </section>
        </article>

        <article v-if="activeTab === 'payments' && activeMode === 'list'" class="panel wide">
          <div class="panel-header">
            <h2>Pagos registrados</h2>
            <div class="filter-bar">
              <label class="search-box"><Search :size="17" /><input v-model="filters.payments" type="search" placeholder="Buscar pago o alumno" /></label>
              <select v-model="filters.paymentStatus" class="filter-select">
                <option value="">Todos los estados</option>
                <option value="PENDING">Pendiente</option>
                <option value="PAID">Pagado</option>
                <option value="OVERDUE">Vencido</option>
              </select>
            </div>
          </div>
          <div class="table">
            <div class="table-row table-head">
              <span>Alumno</span>
              <span>Concepto</span>
              <span>Vence</span>
              <span>Acciones</span>
            </div>
            <div v-for="payment in filteredPayments" :key="payment.id" class="table-row">
              <span><strong>{{ payment.student.full_name }}</strong><small>S/ {{ payment.amount }}</small></span>
              <span>{{ payment.concept }}</span>
              <span>{{ payment.due_date }} <mark :class="payment.status === 'PAID' ? 'ok' : 'warn'">{{ payment.status_label }}</mark></span>
              <span class="row-actions">
                <button class="ghost-button" type="button" @click="editPayment(payment)">Editar</button>
                <button v-if="payment.status !== 'PAID'" class="ghost-button" type="button" @click="updatePaymentStatus(payment, 'PAID')">Pagado</button>
                <button v-if="payment.status !== 'PENDING'" class="ghost-button" type="button" @click="updatePaymentStatus(payment, 'PENDING')">Pendiente</button>
                <button v-if="payment.status !== 'OVERDUE'" class="ghost-button" type="button" @click="updatePaymentStatus(payment, 'OVERDUE')">Vencido</button>
                <button class="danger-button" type="button" @click="deleteItem('payments', payment.id)">Eliminar</button>
              </span>
            </div>
            <p v-if="!filteredPayments.length && !loading" class="empty-state">No hay pagos para los filtros actuales.</p>
          </div>
        </article>

        <article v-if="activeTab === 'attendance'" class="panel wide">
          <div class="panel-header">
            <h2>Asistencia</h2>
          </div>
          <form class="data-form inline-form" @submit.prevent="createAttendanceSession">
            <label>
              Grupo
              <select v-model="attendanceForm.class_group_id" required>
                <option value="">Seleccionar grupo</option>
                <option v-for="group in classGroups" :key="group.id" :value="group.id">{{ group.name }} - {{ groupDayText(group) }}</option>
              </select>
            </label>
            <label>
              Fecha
              <input v-model="attendanceForm.date" required type="date" />
            </label>
            <label>
              Notas
              <input v-model="attendanceForm.notes" type="text" />
            </label>
            <button class="primary" type="submit">Crear sesion</button>
          </form>
          <div class="attendance-list">
            <section v-for="session in attendanceSessions" :key="session.id" class="mini-panel">
              <div class="panel-header">
                <h2>{{ session.class_group.name }} - {{ session.date }}</h2>
              </div>
              <div class="table compact-table">
                <div v-for="record in session.records" :key="record.id" class="table-row">
                  <span><strong>{{ record.student.full_name }}</strong><small>{{ record.status_label }}</small></span>
                  <span class="row-actions">
                    <button class="ghost-button" type="button" @click="updateAttendance(record, 'PRESENT')">Presente</button>
                    <button class="ghost-button" type="button" @click="updateAttendance(record, 'LATE')">Tardanza</button>
                    <button class="ghost-button" type="button" @click="updateAttendance(record, 'JUSTIFIED')">Justificado</button>
                    <button class="danger-button" type="button" @click="updateAttendance(record, 'ABSENT')">Falta</button>
                  </span>
                </div>
              </div>
            </section>
            <p v-if="!attendanceSessions.length && !loading" class="empty-state">Todavia no hay sesiones de asistencia.</p>
          </div>
        </article>

        <article v-if="activeTab === 'progress'" class="panel wide">
          <div class="panel-header">
            <h2>Progreso fisico</h2>
          </div>
          <form class="data-form" @submit.prevent="createProgress">
            <div class="form-grid">
              <label>
                Alumno
                <select v-model="progressForm.student_id" required>
                  <option value="">Seleccionar alumno</option>
                  <option v-for="student in students" :key="student.id" :value="student.id">{{ student.full_name }}</option>
                </select>
              </label>
              <label>
                Fecha
                <input v-model="progressForm.date" required type="date" />
              </label>
            </div>
            <div class="form-grid">
              <label>Peso kg<input v-model="progressForm.weight_kg" step="0.01" type="number" /></label>
              <label>Talla cm<input v-model="progressForm.height_cm" step="0.01" type="number" /></label>
            </div>
            <div class="form-grid">
              <label>Fuerza<input v-model="progressForm.strength" min="0" max="10" type="number" /></label>
              <label>Resistencia<input v-model="progressForm.endurance" min="0" max="10" type="number" /></label>
              <label>Coordinacion<input v-model="progressForm.coordination" min="0" max="10" type="number" /></label>
              <label>Flexibilidad<input v-model="progressForm.flexibility" min="0" max="10" type="number" /></label>
            </div>
            <label>Observaciones<textarea v-model="progressForm.notes" rows="3"></textarea></label>
            <button class="primary" type="submit">Guardar evaluacion</button>
          </form>
          <div class="table">
            <div class="table-row table-head">
              <span>Alumno</span><span>Fecha</span><span>Metricas</span><span>Observaciones</span>
            </div>
            <div v-for="item in progressItems" :key="item.id" class="table-row">
              <span><strong>{{ item.student.full_name }}</strong><small>{{ item.weight_kg }} kg / {{ item.height_cm }} cm</small></span>
              <span>{{ item.date }}</span>
              <span>F{{ item.strength }} R{{ item.endurance }} C{{ item.coordination }} FL{{ item.flexibility }}</span>
              <span>{{ item.notes || '-' }}</span>
            </div>
          </div>
        </article>

        <article v-if="activeTab === 'announcements'" class="panel wide">
          <div class="panel-header">
            <h2>Comunicados</h2>
          </div>
          <form class="data-form" @submit.prevent="createAnnouncement">
            <label>Titulo<input v-model="announcementForm.title" required type="text" /></label>
            <label>Mensaje<textarea v-model="announcementForm.body" required rows="4"></textarea></label>
            <label>
              Destinatario
              <select v-model="announcementForm.parent_id">
                <option value="">Todos los padres</option>
                <option v-for="parent in parents" :key="parent.id" :value="parent.id">{{ parent.full_name }}</option>
              </select>
            </label>
            <button class="primary" type="submit">Publicar comunicado</button>
          </form>
          <ul class="notice-list">
            <li v-for="announcement in announcements" :key="announcement.id">
              <strong>{{ announcement.title }}</strong><br />
              {{ announcement.body }}<br />
              <small>{{ announcement.audience_label }}</small>
            </li>
          </ul>
        </article>

        <article v-if="activeTab === 'reports'" class="panel wide">
          <div class="panel-header">
            <h2>Reportes</h2>
            <a class="primary compact" :href="exportReportUrl" target="_blank">Exportar CSV</a>
          </div>
          <section class="metrics-grid compact-metrics">
            <article class="metric"><span>Alumnos activos</span><strong>{{ reports?.students_active || 0 }}</strong></article>
            <article class="metric"><span>Pagos pendientes</span><strong>{{ reports?.payments_pending || 0 }}</strong></article>
            <article class="metric"><span>Ingresos</span><strong>S/ {{ reports?.income_total || 0 }}</strong></article>
            <article class="metric"><span>Evaluaciones</span><strong>{{ reports?.progress_evaluations || 0 }}</strong></article>
          </section>
          <ul class="notice-list">
            <li v-for="item in reports?.attendance || []" :key="item.status">{{ item.status }}: {{ item.total }}</li>
          </ul>
        </article>

        <article v-if="activeTab === 'settings'" class="panel form-panel">
          <div class="panel-header">
            <h2>Configuracion</h2>
          </div>
          <form class="data-form" @submit.prevent="saveSettings">
            <label>Academia<input v-model="settings.academy_name" required type="text" /></label>
            <label>Profesor<input v-model="settings.teacher_name" required type="text" /></label>
            <div class="form-grid">
              <label>Telefono<input v-model="settings.phone" type="tel" /></label>
              <label>Mensualidad por defecto<input v-model="settings.default_monthly_fee" step="0.01" type="number" /></label>
            </div>
            <label>Direccion<input v-model="settings.address" type="text" /></label>
            <button class="primary" type="submit">Guardar configuracion</button>
          </form>
        </article>

        <article v-if="isCrudTab && activeMode === 'form'" class="panel form-panel">
          <div class="panel-header">
            <h2>
              {{
                activeTab === 'students'
                  ? isEditingCurrentTab ? 'Editar alumno' : 'Nuevo alumno'
                  : activeTab === 'parents'
                    ? isEditingCurrentTab ? 'Editar padre' : 'Nuevo padre'
                    : activeTab === 'groups'
                      ? isEditingCurrentTab ? 'Editar horario' : 'Nuevo horario'
                      : isEditingCurrentTab ? 'Editar pago' : 'Nuevo pago'
              }}
            </h2>
          </div>

          <form v-if="activeTab === 'students'" class="data-form" @submit.prevent="createStudent">
            <label>
              Padre
              <select v-model="studentForm.parent_id" required>
                <option value="">Seleccionar padre</option>
                <option v-for="parent in parents" :key="parent.id" :value="parent.id">{{ parent.full_name }}</option>
              </select>
            </label>
            <label>
              Grupo
              <select v-model="studentForm.class_group_id">
                <option value="">Sin grupo</option>
                <option v-for="group in classGroups" :key="group.id" :value="group.id">
                  {{ group.name }} - {{ groupDayText(group) }} {{ group.start_time }}
                </option>
              </select>
            </label>
            <label>
              Nombres
              <input v-model="studentForm.first_name" required type="text" />
            </label>
            <label>
              Apellidos
              <input v-model="studentForm.last_name" required type="text" />
            </label>
            <label>
              Fecha de nacimiento
              <input v-model="studentForm.birth_date" required type="date" />
            </label>
            <div class="form-grid">
              <label>
                Peso kg
                <input v-model="studentForm.weight_kg" min="0" step="0.01" type="number" />
              </label>
              <label>
                Talla cm
                <input v-model="studentForm.height_cm" min="0" step="0.01" type="number" />
              </label>
            </div>
            <label>
              Notas medicas
              <textarea v-model="studentForm.medical_notes" rows="3"></textarea>
            </label>
            <div class="form-actions">
              <button class="primary" type="submit">{{ isEditingCurrentTab ? 'Actualizar alumno' : 'Guardar alumno' }}</button>
              <button v-if="isEditingCurrentTab" class="secondary" type="button" @click="cancelEdit">Cancelar</button>
            </div>
          </form>

          <form v-else-if="activeTab === 'parents'" class="data-form" @submit.prevent="createParent">
            <div class="form-grid">
              <label>
                Nombres
                <input v-model="parentForm.first_name" required type="text" />
              </label>
              <label>
                Apellidos
                <input v-model="parentForm.last_name" required type="text" />
              </label>
            </div>
            <label>
              Telefono
              <input v-model="parentForm.phone" required type="tel" />
            </label>
            <label>
              DNI
              <input v-model="parentForm.dni" required type="text" />
            </label>
            <label>
              Correo
              <input v-model="parentForm.email" type="email" />
            </label>
            <label>
              Direccion
              <input v-model="parentForm.address" type="text" />
            </label>
            <label>
              Telefono de emergencia
              <input v-model="parentForm.emergency_phone" type="tel" />
            </label>
            <div class="form-actions">
              <button class="primary" type="submit">{{ isEditingCurrentTab ? 'Actualizar padre' : 'Guardar padre' }}</button>
              <button v-if="isEditingCurrentTab" class="secondary" type="button" @click="cancelEdit">Cancelar</button>
            </div>
          </form>

          <form v-else-if="activeTab === 'groups'" class="data-form" @submit.prevent="createGroup">
            <label>
              Nombre del grupo
              <input v-model="groupForm.name" required type="text" placeholder="Kids funcional 6-9" />
            </label>
            <fieldset class="field-group">
              <legend>Dias</legend>
              <div class="day-picker">
                <button
                  v-for="day in dayOptions"
                  :key="day.value"
                  :class="{ active: groupForm.days_of_week.includes(day.value) }"
                  type="button"
                  @click="toggleGroupDay(day.value)"
                >
                  {{ day.label }}
                </button>
              </div>
            </fieldset>
            <div class="form-grid">
              <label>
                Inicio
                <input v-model="groupForm.start_time" required type="time" />
              </label>
              <label>
                Fin
                <input v-model="groupForm.end_time" required type="time" />
              </label>
            </div>
            <div class="form-grid">
              <label>
                Cupos
                <input v-model="groupForm.capacity" min="1" required type="number" />
              </label>
              <label>
                Rango edad
                <input v-model="groupForm.age_range" type="text" placeholder="6 a 9 anos" />
              </label>
            </div>
            <fieldset class="field-group">
              <legend>Color</legend>
              <div class="color-picker">
                <button
                  v-for="color in groupColors"
                  :key="color"
                  :class="{ active: groupForm.color === color }"
                  :style="{ background: color }"
                  :title="color"
                  type="button"
                  @click="groupForm.color = color"
                ></button>
              </div>
            </fieldset>
            <div class="form-actions">
              <button class="primary" type="submit">{{ isEditingCurrentTab ? 'Actualizar horario' : 'Guardar horario' }}</button>
              <button v-if="isEditingCurrentTab" class="secondary" type="button" @click="cancelEdit">Cancelar</button>
            </div>
          </form>

          <form v-else class="data-form" @submit.prevent="createPayment">
            <label>
              Alumno
              <select v-model="paymentForm.student_id" required>
                <option value="">Seleccionar alumno</option>
                <option v-for="student in students" :key="student.id" :value="student.id">{{ student.full_name }}</option>
              </select>
            </label>
            <label>
              Concepto
              <input v-model="paymentForm.concept" required type="text" />
            </label>
            <div class="form-grid">
              <label>
                Monto
                <input v-model="paymentForm.amount" min="0" required step="0.01" type="number" />
              </label>
              <label>
                Vencimiento
                <input v-model="paymentForm.due_date" required type="date" />
              </label>
            </div>
            <label>
              Fecha de pago
              <input v-model="paymentForm.paid_date" type="date" />
            </label>
            <label>
              Estado
              <select v-model="paymentForm.status">
                <option value="PENDING">Pendiente</option>
                <option value="PAID">Pagado</option>
                <option value="OVERDUE">Vencido</option>
              </select>
            </label>
            <label>
              Notas
              <textarea v-model="paymentForm.notes" rows="3"></textarea>
            </label>
            <div class="form-actions">
              <button class="primary" type="submit">{{ isEditingCurrentTab ? 'Actualizar pago' : 'Guardar pago' }}</button>
              <button v-if="isEditingCurrentTab" class="secondary" type="button" @click="cancelEdit">Cancelar</button>
            </div>
          </form>
        </article>
      </section>
      <div v-if="confirmModal.open" class="modal-backdrop">
        <section class="modal-panel" role="dialog" aria-modal="true">
          <h2>Confirmar eliminacion</h2>
          <p>Esta accion eliminara {{ confirmModal.label }}. No se puede deshacer.</p>
          <div class="form-actions">
            <button class="danger-button large" type="button" @click="confirmDelete">Eliminar</button>
            <button class="secondary" type="button" @click="closeConfirm">Cancelar</button>
          </div>
        </section>
      </div>
    </section>
  </main>
</template>
