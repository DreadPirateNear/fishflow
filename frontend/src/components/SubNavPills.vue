<script setup>
import { computed } from 'vue'
import { Activity, Waves, CloudSun, Moon } from 'lucide-vue-next'
import { t } from '../i18n/index.js'

const props = defineProps({
  activeTab: {
    type: String,
    default: 'activity'
  },
  showActivity: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['changeTab'])

const tabs = computed(() => {
  const list = []
  if (props.showActivity) {
    list.push({ id: 'activity', label: t('activity'), icon: Activity })
  }
  list.push({ id: 'marine', label: t('marine'), icon: Waves })
  list.push({ id: 'weather', label: t('weather'), icon: CloudSun })
  list.push({ id: 'sun_moon', label: t('sun_moon'), icon: Moon })
  return list
})
</script>

<template>
  <div class="px-3 sm:px-4 py-1.5 select-none">
    <div class="bg-black/40 backdrop-blur-md rounded-2xl p-1 flex items-center justify-between border border-white/10 shadow-lg gap-1">
      <button
        v-for="item in tabs"
        :key="item.id"
        @click="emit('changeTab', item.id)"
        class="flex-1 flex flex-col items-center justify-center py-2 px-1 rounded-xl transition-all duration-200 relative text-center group"
        :class="activeTab === item.id ? 'bg-sky-500/25 text-white shadow-sm border border-sky-400/35' : 'text-white/50 hover:text-white/80 hover:bg-white/5'"
      >
        <component 
          :is="item.icon" 
          class="w-4 h-4 mb-1 transition-transform group-hover:scale-110" 
          :class="activeTab === item.id ? 'text-sky-400' : 'text-white/60'"
        />
        <span class="text-[10px] font-semibold tracking-tight leading-tight whitespace-nowrap">
          {{ item.label }}
        </span>
      </button>
    </div>
  </div>
</template>
