<script setup>
import { computed } from 'vue'
import { Globe, TrendingUp, Star } from 'lucide-vue-next'
import { t } from '../i18n/index.js'

const props = defineProps({
  currentTab: {
    type: String,
    default: 'forecast'
  }
})

const emit = defineEmits(['changeTab'])

const navItems = computed(() => [
  { id: 'map', label: t('map'), icon: Globe },
  { id: 'forecast', label: t('forecast'), icon: TrendingUp },
  { id: 'spots', label: t('spots'), icon: Star }
])
</script>

<template>
  <nav class="bg-black/90 backdrop-blur-xl border-t border-white/10 px-4 py-2 flex items-center justify-around select-none z-50">
    <button
      v-for="item in navItems"
      :key="item.id"
      @click="emit('changeTab', item.id)"
      class="flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition duration-150"
      :class="currentTab === item.id ? 'text-sky-400 font-semibold' : 'text-white/45 hover:text-white/80'"
    >
      <div 
        class="p-1 rounded-xl transition"
        :class="currentTab === item.id ? 'bg-sky-500/15' : ''"
      >
        <component :is="item.icon" class="w-5 h-5" />
      </div>
      <span class="text-[10px] tracking-tight mt-0.5">
        {{ item.label }}
      </span>
    </button>
  </nav>
</template>
