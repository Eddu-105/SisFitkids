<script setup>
import { computed } from 'vue'
import { dayOptions, groupDays } from '../constants/schedule'

const props = defineProps({
  group: {
    type: Object,
    default: null,
  },
})

const schedule = computed(() => {
  if (!props.group) {
    return []
  }
  const days = groupDays(props.group)
  return dayOptions.map((day) => ({
    ...day,
    group: days.includes(day.value) ? props.group : null,
  }))
})
</script>

<template>
  <section class="mini-week-calendar">
    <article v-for="day in schedule" :key="day.value" class="mini-calendar-day">
      <span>{{ day.label }}</span>
      <strong v-if="day.group" :style="{ borderColor: day.group.color }">
        {{ day.group.start_time }} - {{ day.group.end_time }}
      </strong>
      <small v-else>Libre</small>
    </article>
  </section>
</template>
