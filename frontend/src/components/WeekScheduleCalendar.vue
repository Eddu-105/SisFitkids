<script setup>
import { computed } from 'vue'
import { dayOptions, groupDays } from '../constants/schedule'

const props = defineProps({
  groups: {
    type: Array,
    default: () => [],
  },
})

const weeklyCalendar = computed(() => dayOptions.map((day) => ({
  ...day,
  groups: props.groups
    .filter((group) => group.is_active && groupDays(group).includes(day.value))
    .sort((first, second) => first.start_time.localeCompare(second.start_time)),
})))
</script>

<template>
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
</template>
