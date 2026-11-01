<script setup>
import { computed } from 'vue'
import { currentLang } from '../i18n/index.js'

const props = defineProps({
  days: {
    type: Array,
    default: () => []
  },
  selectedDate: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['selectDate'])

const EN_DAYS = {
  'Lun': 'Mon', 'Mar': 'Tue', 'Mer': 'Wed', 'Gio': 'Thu', 'Ven': 'Fri', 'Sab': 'Sat', 'Dom': 'Sun',
  'Oggi': 'Today', 'Domani': 'Tomorrow', 'Ieri': 'Yesterday'
}

const getLocalizedDayName = (dayName) => {
  if (currentLang.value === 'en') {
    return EN_DAYS[dayName] || dayName
  }
  return dayName
}
</script>

<template>
  <div class="px-2 py-2 overflow-x-auto no-scrollbar flex items-center justify-between border-b border-white/10 select-none">
    <button
      v-for="d in days"
      :key="d.date"
      @click="emit('selectDate', d.date)"
      class="flex flex-col items-center justify-center flex-1 min-w-[50px] py-1 transition relative group"
    >
      <!-- Day number -->
      <span 
        class="text-sm font-semibold transition"
        :class="d.date === selectedDate ? 'text-white font-bold' : 'text-white/60 group-hover:text-white/90'"
      >
        {{ d.day_number }}
      </span>

      <!-- Day name or Oggi -->
      <span 
        class="text-[11px] font-medium transition"
        :class="d.date === selectedDate ? 'text-white font-semibold' : 'text-white/40 group-hover:text-white/70'"
      >
        {{ getLocalizedDayName(d.day_name) }}
      </span>

      <!-- Active indicator underline (as in Screenshot 1) -->
      <div 
        v-if="d.date === selectedDate"
        class="absolute -bottom-2 w-7 h-[3px] bg-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.7)]"
      />
    </button>
  </div>
</template>
