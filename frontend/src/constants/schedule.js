export const dayOptions = [
  { value: 1, label: 'Lunes' },
  { value: 2, label: 'Martes' },
  { value: 3, label: 'Miercoles' },
  { value: 4, label: 'Jueves' },
  { value: 5, label: 'Viernes' },
  { value: 6, label: 'Sabado' },
  { value: 7, label: 'Domingo' },
]

export const groupColors = ['#0d7467', '#1d4ed8', '#be123c', '#7c3aed', '#b45309', '#047857', '#c2410c', '#0369a1']

export function groupDays(group) {
  return group?.days_of_week?.length ? group.days_of_week.map(Number) : [Number(group?.day_of_week)].filter(Boolean)
}

export function groupDayText(group) {
  return group?.day_labels?.length ? group.day_labels.join(', ') : group?.day_label
}
