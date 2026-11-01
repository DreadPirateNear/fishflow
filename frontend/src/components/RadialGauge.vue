<script setup>
import { computed } from 'vue'
import { t, currentLang } from '../i18n/index.js'

const props = defineProps({
  score: {
    type: Number,
    default: 0
  },
  rating: {
    type: String,
    default: 'Molto bassa'
  }
})

// Circumference of radius 52 is ~326.72
const RADIUS = 52
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

const strokeDashoffset = computed(() => {
  const clamped = Math.max(0, Math.min(100, props.score))
  return CIRCUMFERENCE * (1 - clamped / 100)
})

const badgeColorClasses = computed(() => {
  const r = (props.rating || '').toLowerCase()
  if (r.includes('eccellente')) {
    return 'bg-emerald-500/20 text-emerald-300 border-emerald-400/35 shadow-[0_0_15px_rgba(16,185,129,0.25)]'
  }
  if (r.includes('buona')) {
    return 'bg-teal-500/20 text-teal-300 border-teal-400/35 shadow-[0_0_12px_rgba(20,184,166,0.2)]'
  }
  if (r.includes('media')) {
    return 'bg-cyan-500/20 text-cyan-300 border-cyan-400/35'
  }
  if (r.includes('bassa') && !r.includes('molto')) {
    return 'bg-sky-500/20 text-sky-300 border-sky-400/30'
  }
  return 'bg-white/10 text-white/70 border-white/15'
})

const translatedRating = computed(() => {
  const r = (props.rating || '').toLowerCase()
  if (r.includes('eccellente')) return t('rating_excellent')
  if (r.includes('buona')) return t('rating_good')
  if (r.includes('media')) return t('rating_average')
  if (r.includes('molto')) return t('rating_very_low')
  if (r.includes('bassa')) return t('rating_low')
  return props.rating
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-1 sm:py-2.5 select-none">
    <div class="relative w-36 h-36 xl:w-40 xl:h-40 flex items-center justify-center">
      <!-- Glow ambient background -->
      <div 
        class="absolute w-32 h-32 rounded-full opacity-25 blur-xl transition duration-500 pointer-events-none"
        :class="score >= 65 ? 'bg-cyan-400' : 'bg-blue-600'"
      />

      <!-- SVG Circular Activity Gauge -->
      <svg class="w-full h-full -rotate-90 transform" viewBox="0 0 130 130">
        <defs>
          <linearGradient id="fishflowGaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0284c7" />
            <stop offset="50%" stop-color="#06b6d4" />
            <stop offset="100%" stop-color="#10b981" />
          </linearGradient>
          <filter id="gaugeGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <!-- Base Background Track -->
        <circle
          cx="65"
          cy="65"
          :r="RADIUS"
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          stroke-width="8"
        />

        <!-- Dynamic Animated Progress Arc -->
        <circle
          cx="65"
          cy="65"
          :r="RADIUS"
          fill="none"
          stroke="url(#fishflowGaugeGrad)"
          stroke-width="8"
          stroke-linecap="round"
          :stroke-dasharray="CIRCUMFERENCE"
          :stroke-dashoffset="strokeDashoffset"
          class="transition-all duration-700 ease-out"
          filter="url(#gaugeGlow)"
        />
      </svg>

      <!-- Center Score Display -->
      <div class="absolute inset-0 flex flex-col items-center justify-center text-center select-none pointer-events-none px-3">
        <span class="text-4xl xl:text-[44px] font-black tracking-tight text-white font-sans drop-shadow-md leading-none">
          {{ score }}
        </span>
        <div class="mt-1 flex flex-col items-center leading-none">
          <span class="text-[9px] font-bold text-sky-400 tracking-wider uppercase">
            {{ currentLang === 'it' ? 'Indice' : 'Index' }}
          </span>
          <span class="text-[7.5px] font-semibold text-sky-200/70 tracking-wider uppercase mt-0.5">
            {{ currentLang === 'it' ? 'in tempo reale' : 'real time' }}
          </span>
        </div>
      </div>
    </div>

    <!-- FishFlow Qualitative Rating Pill -->
    <div class="mt-2 text-center">
      <span 
        class="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-semibold border transition duration-300"
        :class="badgeColorClasses"
      >
        {{ translatedRating }}
      </span>
    </div>
  </div>
</template>
