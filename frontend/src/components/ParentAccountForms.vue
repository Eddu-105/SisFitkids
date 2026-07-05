<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  parent: {
    type: Object,
    required: true,
  },
  savingProfile: {
    type: Boolean,
    default: false,
  },
  savingPassword: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['save-profile', 'change-password'])

const profileForm = ref({})
const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

function syncProfileForm(parent) {
  profileForm.value = {
    first_name: parent?.first_name || '',
    last_name: parent?.last_name || '',
    phone: parent?.phone || '',
    email: parent?.email || '',
    address: parent?.address || '',
    emergency_phone: parent?.emergency_phone || '',
  }
}

function resetPasswordForm() {
  passwordForm.value = {
    current_password: '',
    new_password: '',
    confirm_password: '',
  }
}

function submitPassword() {
  emit('change-password', { ...passwordForm.value, reset: resetPasswordForm })
}

watch(() => props.parent, syncProfileForm, { immediate: true })
</script>

<template>
  <section class="account-forms">
    <article class="panel profile-edit-panel">
      <div class="panel-header">
        <h2>Mis datos</h2>
      </div>
      <form class="data-form" @submit.prevent="emit('save-profile', { ...profileForm })">
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
    </article>

    <article class="panel profile-edit-panel">
      <div class="panel-header">
        <h2>Cambiar contrasena</h2>
      </div>
      <form class="data-form" @submit.prevent="submitPassword">
        <label>
          Contrasena actual
          <input v-model="passwordForm.current_password" autocomplete="current-password" required type="password" />
        </label>
        <div class="form-grid">
          <label>
            Nueva contrasena
            <input v-model="passwordForm.new_password" autocomplete="new-password" minlength="8" required type="password" />
          </label>
          <label>
            Confirmar contrasena
            <input v-model="passwordForm.confirm_password" autocomplete="new-password" minlength="8" required type="password" />
          </label>
        </div>
        <div class="form-actions">
          <button class="primary" :disabled="savingPassword" type="submit">
            {{ savingPassword ? 'Actualizando...' : 'Actualizar contrasena' }}
          </button>
        </div>
      </form>
    </article>
  </section>
</template>
