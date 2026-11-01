<script setup>
import { computed } from 'vue'
import { MapPin, Bell, Navigation, Waves, Globe, TrendingUp, Star } from 'lucide-vue-next'
import { currentLang, toggleLanguage, t } from '../i18n/index.js'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  spotName: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  currentTab: {
    type: String,
    default: 'forecast'
  }
})

const emit = defineEmits(['openSearch', 'useGps', 'openFavorites', 'changeTab'])

const navTabs = computed(() => [
  { id: 'map', label: t('map'), icon: Globe },
  { id: 'forecast', label: t('forecast'), icon: TrendingUp },
  { id: 'spots', label: t('spots'), icon: Star }
])
</script>

<template>
  <header class="pt-3 pb-2.5 px-4 md:px-6 flex items-center justify-between border-b border-white/10 bg-slate-950/40 backdrop-blur-md">
    <!-- Left: App Brand & View Title / Spot -->
    <div class="flex items-center gap-4">
      <!-- Desktop Brand Logo -->
      <div class="hidden sm:flex items-center gap-2 pr-2 border-r border-white/10">
        <div class="w-9 h-9 rounded-xl bg-[#071a33] border border-cyan-400/30 flex items-center justify-center shadow-lg shadow-sky-500/20 p-1">
          <img src="/fish.svg" alt="FishFlow" class="w-full h-full object-contain" />
        </div>
        <span class="text-base font-black tracking-tight text-white">Fish<span class="text-sky-400">Flow</span></span>
      </div>

      <div class="flex items-center gap-2.5">
        <!-- Mobile Brand Icon -->
        <div class="sm:hidden w-8 h-8 rounded-xl bg-[#071a33] border border-cyan-400/30 flex items-center justify-center p-1 shrink-0 shadow-md">
          <img src="/fish.svg" alt="FishFlow" class="w-full h-full object-contain" />
        </div>

        <div>
          <h1 class="text-xl sm:text-2xl font-bold tracking-tight text-white leading-tight">
            {{ title || t('activity') }}
          </h1>
          <button 
            @click="emit('openSearch')"
            class="flex items-center gap-1.5 text-xs text-sky-200/80 hover:text-white transition mt-0.5 group"
          >
            <MapPin class="w-3.5 h-3.5 text-sky-400 group-hover:scale-110 transition shrink-0" />
            <span class="font-medium truncate max-w-[170px] sm:max-w-xs">{{ spotName || t('use_gps') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Center: Desktop Navigation Tabs (Visible on md and up) -->
    <div class="hidden md:flex items-center gap-1 bg-white/5 p-1 rounded-2xl border border-white/10">
      <button
        v-for="tab in navTabs"
        :key="tab.id"
        @click="emit('changeTab', tab.id)"
        class="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition"
        :class="currentTab === tab.id ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30' : 'text-white/60 hover:text-white hover:bg-white/5'"
      >
        <component :is="tab.icon" class="w-4 h-4" />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- Right: Actions (Language, GPS, Favorites) -->
    <div class="flex items-center gap-2">
      <!-- Language Switcher IT | EN -->
      <button 
        @click="toggleLanguage"
        title="Cambia lingua / Switch language"
        class="h-9 px-2.5 rounded-full bg-white/10 hover:bg-white/20 active:scale-95 flex items-center gap-1 transition border border-white/10 text-[11px] font-bold text-white shadow-sm"
      >
        <span :class="currentLang === 'it' ? 'text-sky-400 font-extrabold' : 'text-white/40'">IT</span>
        <span class="text-white/25 text-[10px]">|</span>
        <span :class="currentLang === 'en' ? 'text-sky-400 font-extrabold' : 'text-white/40'">EN</span>
      </button>

      <!-- GPS Geolocation Action -->
      <button 
        @click="emit('useGps')"
        :title="t('use_gps')"
        class="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 active:scale-95 flex items-center justify-center transition border border-white/10 text-white"
        :class="{ 'animate-spin text-sky-400 border-sky-400/50': loading }"
      >
        <Navigation class="w-4 h-4" />
      </button>

      <!-- Favorites / Saved Spots -->
      <button 
        @click="emit('openFavorites')"
        :title="t('favorites')"
        class="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 active:scale-95 flex items-center justify-center transition border border-white/10 text-white"
      >
        <Bell class="w-4 h-4" />
      </button>
    </div>
  </header>
</template>
