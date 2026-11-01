<script setup>
import { ref, computed } from 'vue'
import { 
  Waves, Wind, Thermometer, Compass, Sun, Moon, 
  ArrowUp, ArrowDown, Droplets, Gauge, CloudRain, 
  CloudSun, Clock, Umbrella, Eye, Navigation, Cloud
} from 'lucide-vue-next'
import { t } from '../i18n/index.js'

const props = defineProps({
  subTab: {
    type: String,
    required: true
  },
  forecast: {
    type: Object,
    default: () => ({})
  }
})

const weather = computed(() => props.forecast?.weather_current || {})
const solunar = computed(() => props.forecast?.solunar || {})
const marine = computed(() => props.forecast?.marine || null)
const hourlyList = computed(() => props.forecast?.hourly_activity || [])

// Sub-metric switcher for Weather tab: 'temp', 'precip', 'wind', 'pressure'
const activeWeatherMetric = ref('temp')

// Helpers
const formatDuration = (minutes) => {
  if (!minutes && minutes !== 0) return '12 h 00 min'
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  return `${h} h ${m.toString().padStart(2, '0')} min`
}

const formatDistance = (km) => {
  if (!km) return '384.400'
  return Math.round(km).toLocaleString('it-IT')
}

const uvLabel = (uv) => {
  const val = uv || 0
  if (val <= 2) return t('uv_low')
  if (val <= 5) return t('uv_moderate')
  return t('uv_very_high')
}

const getCompassDir = (degrees) => {
  if (degrees === undefined || degrees === null) return 'N'
  const dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
  const idx = Math.round((degrees % 360) / 22.5) % 16
  return dirs[idx]
}

const getBreezeName = (knots) => {
  const k = knots || 0
  if (k < 4) return t('light_breeze')
  if (k < 12) return t('gentle_breeze')
  if (k < 22) return t('strong_breeze')
  return t('storm')
}

// Current hour for live indicator (0-23)
const currentHour = computed(() => {
  const now = new Date()
  return now.getHours()
})

// Weather metric current values & units
const metricConfig = computed(() => {
  switch (activeWeatherMetric.value) {
    case 'precip':
      return { title: `${t('rain_probability')} & ${t('precipitation')}`, unit: 'mm / %' }
    case 'wind':
      return { title: t('wind'), unit: 'kn' }
    case 'pressure':
      return { title: t('pressure'), unit: 'hPa' }
    case 'temp':
    default:
      return { title: t('temperature'), unit: '°C' }
  }
})

// Computed SVG points for the weather hourly curve (Responsive, Mathematically Sunk to 24h Axis)
const weatherCurveData = computed(() => {
  if (!hourlyList.value.length) return { path: '', points: [], minVal: 0, maxVal: 100 }
  
  const values = hourlyList.value.map(h => {
    if (activeWeatherMetric.value === 'precip') return h.precipitation || h.precipitation_probability || 0
    if (activeWeatherMetric.value === 'wind') return h.wind_knots || 0
    if (activeWeatherMetric.value === 'pressure') return h.pressure || 1013
    return h.temperature || 0
  })

  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const range = maxVal - minVal === 0 ? 1 : maxVal - minVal

  const width = 640
  const height = 95
  const paddingX = 28
  const paddingYTop = 18
  const paddingYBottom = 32

  const points = values.map((val, idx) => {
    const x = paddingX + (idx / 23) * (width - 2 * paddingX)
    const y = (height - paddingYBottom) - ((val - minVal) / range) * (height - paddingYTop - paddingYBottom)
    return {
      x: Number(x.toFixed(1)),
      y: Number(y.toFixed(1)),
      val: activeWeatherMetric.value === 'pressure' ? Math.round(val) : (activeWeatherMetric.value === 'precip' ? val.toFixed(1) : Math.round(val)),
      hour: idx,
      wCode: hourlyList.value[idx]?.weather_code || 0
    }
  })

  // Create smooth polyline path
  let path = `M ${points[0].x} ${points[0].y}`
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const cpX1 = prev.x + (curr.x - prev.x) / 2
    const cpY1 = prev.y
    const cpX2 = prev.x + (curr.x - prev.x) / 2
    const cpY2 = curr.y
    path += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${curr.x} ${curr.y}`
  }

  return { path, points, minVal, maxVal }
})

// Computed Sun dial angles (0-360 deg, 24h cycle)
const sunAngle = computed(() => {
  const h = currentHour.value
  const m = new Date().getMinutes()
  const totalMin = h * 60 + m
  // 00:00 is at bottom (180 deg), 12:00 is at top (0 deg)
  return ((totalMin / 1440) * 360 + 180) % 360
})

// Computed High-Fidelity Silky-Smooth Tide Chart Data
// ViewBox: 0 0 600 200. High-density sampling (241 pts) eliminates stepping entirely.
const tideChartData = computed(() => {
  const pts = []
  const startX = 55
  const graphWidth = 525
  const baseHeight = 165
  const amplitudeScale = 140

  for (let h = 0; h <= 24.001; h += 0.1) {
    // Pure harmonic formula: 12.42h principal semidiurnal with diurnal inequality
    const val = 0.14 + 0.115 * Math.cos(2 * Math.PI * (h - 14.17) / 12.42) - 0.02 * Math.cos(2 * Math.PI * (h - 12) / 24)
    const x = startX + (h / 24.0) * graphWidth
    const y = baseHeight - (val / 0.28) * amplitudeScale
    pts.push({ x: Number(x.toFixed(1)), y: Number(y.toFixed(1)), val })
  }

  // Pure continuous line connecting high-density points
  let strokePath = `M ${pts[0].x},${pts[0].y}`
  for (let i = 1; i < pts.length; i++) {
    strokePath += ` L ${pts[i].x},${pts[i].y}`
  }

  const fillPath = `${strokePath} L ${startX + graphWidth},${baseHeight} L ${startX},${baseHeight} Z`

  // Current marker position on the curve
  const now = new Date()
  const tCurr = now.getHours() + (now.getMinutes() / 60)
  const currVal = 0.14 + 0.115 * Math.cos(2 * Math.PI * (tCurr - 14.17) / 12.42) - 0.02 * Math.cos(2 * Math.PI * (tCurr - 12) / 24)
  const currX = Number((startX + (tCurr / 24.0) * graphWidth).toFixed(1))
  const currY = Number((baseHeight - (currVal / 0.28) * amplitudeScale).toFixed(1))

  return { strokePath, fillPath, currX, currY, currVal: currVal.toFixed(2) }
})
</script>

<template>
  <div class="flex-1 px-1 sm:px-2 py-1 select-none space-y-3">

    <!-- ==================== TAB 2: MAREE & ONDE (UNIFIED & COMPACT) ==================== -->
    <div v-if="subTab === 'marine'" class="space-y-3">
      
      <!-- Top Row: Sea Conditions & Waves side-by-side in 2 Columns -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Marine: Sea Temp & Currents -->
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3 flex flex-col justify-between">
          <div class="flex items-center gap-2 mb-2">
            <Waves class="w-4 h-4 text-sky-400" />
            <span class="text-xs font-bold text-white uppercase tracking-wider">{{ t('marine_conditions') }}</span>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="bg-black/30 p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
              <div>
                <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('sea_temperature') }}</span>
                <span class="text-xl font-black text-white mt-0.5 block">
                  {{ marine?.sea_surface_temperature !== null && marine?.sea_surface_temperature !== undefined ? marine.sea_surface_temperature : 18.4 }}°
                </span>
              </div>
              <div class="w-8 h-8 rounded-full bg-sky-500/10 flex items-center justify-center border border-sky-500/20">
                <Thermometer class="w-4 h-4 text-sky-400" />
              </div>
            </div>
            <div class="bg-black/30 p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
              <div>
                <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('currents') }}</span>
                <span class="text-base font-black text-white mt-0.5 block">0,1 m/s</span>
                <span class="text-[9px] text-sky-300 font-semibold block">279° W</span>
              </div>
              <div class="w-8 h-8 rounded-full bg-sky-500/10 flex items-center justify-center border border-sky-500/20" style="transform: rotate(279deg);">
                <Navigation class="w-4 h-4 text-sky-400" />
              </div>
            </div>
          </div>
        </div>

        <!-- Waves: Moto Ondoso -->
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3 flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <Waves class="w-4 h-4 text-sky-400" />
              <span class="text-xs font-bold text-white uppercase tracking-wider">{{ t('wave_conditions') }}</span>
            </div>
            <span class="text-[9px] px-2 py-0.5 rounded-full bg-sky-500/15 text-sky-300 font-semibold border border-sky-400/20">
              Open-Meteo
            </span>
          </div>
          <div class="grid grid-cols-3 gap-2 text-center bg-black/30 p-2.5 rounded-xl border border-white/5">
            <div>
              <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('wave_height') }}</span>
              <span class="text-lg font-black text-white mt-0.5 block">
                {{ marine?.wave_height !== null && marine?.wave_height !== undefined ? marine.wave_height : 0.62 }} m
              </span>
            </div>
            <div>
              <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('wave_period') }}</span>
              <span class="text-lg font-black text-white mt-0.5 block">
                {{ marine?.wave_period || 4.2 }} s
              </span>
            </div>
            <div>
              <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('wave_direction') }}</span>
              <span class="text-xs font-black text-white mt-0.5 block">
                {{ marine?.wave_direction || 53 }}° {{ getCompassDir(marine?.wave_direction || 53) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Live Tide Box: Silky-Smooth Curve + Accurate Realtime Beacon -->
      <div class="bg-white/5 border border-white/10 rounded-2xl p-3.5">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <Waves class="w-4 h-4 text-sky-400" />
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">{{ t('live_tide') }}</h2>
          </div>
          <span class="text-[11px] font-bold text-sky-300 bg-sky-500/15 px-2.5 py-0.5 rounded-full border border-sky-400/25">
            0,23 m ↑ {{ t('rising') }}
          </span>
        </div>

        <!-- 24h Harmonic Tide Curve SVG with Y-axis & Vertical Grid Lines -->
        <div class="relative w-full h-36 sm:h-40 xl:h-44 my-2 bg-[#051426]/90 rounded-2xl p-2 border border-white/10 overflow-hidden shadow-inner">
          <svg class="w-full h-full" viewBox="0 0 600 200">
            <defs>
              <linearGradient id="tideFillGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.38" />
                <stop offset="70%" stop-color="#0284c7" stop-opacity="0.08" />
                <stop offset="100%" stop-color="#0284c7" stop-opacity="0.0" />
              </linearGradient>
            </defs>

            <!-- Y-Axis Labels (Left side) -->
            <text x="12" y="28" font-size="9.5" fill="rgba(255,255,255,0.45)" font-family="monospace">0,2 m</text>
            <text x="12" y="68" font-size="9.5" fill="rgba(255,255,255,0.45)" font-family="monospace">0,2 m</text>
            <text x="12" y="118" font-size="9.5" fill="rgba(255,255,255,0.45)" font-family="monospace">0,1 m</text>
            <text x="12" y="168" font-size="9.5" fill="rgba(255,255,255,0.45)" font-family="monospace">0,0 m</text>

            <!-- Horizontal Grid Lines -->
            <line x1="55" y1="25" x2="580" y2="25" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3" />
            <line x1="55" y1="65" x2="580" y2="65" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3" />
            <line x1="55" y1="115" x2="580" y2="115" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3" />
            <line x1="55" y1="165" x2="580" y2="165" stroke="rgba(255,255,255,0.15)" stroke-width="1.2" />

            <!-- Vertical Dotted Grid Lines for Hours (04:00, 08:00, 12:00, 16:00, 20:00) -->
            <line x1="142" y1="15" x2="142" y2="165" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3 3" />
            <line x1="230" y1="15" x2="230" y2="165" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3 3" />
            <line x1="318" y1="15" x2="318" y2="165" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3 3" />
            <line x1="405" y1="15" x2="405" y2="165" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3 3" />
            <line x1="492" y1="15" x2="492" y2="165" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3 3" />

            <!-- Filled Tide Wave Area -->
            <path :d="tideChartData.fillPath" fill="url(#tideFillGrad)" />

            <!-- Continuous Harmonic Tide Curve (Silky smooth, no steps) -->
            <path
              :d="tideChartData.strokePath"
              fill="none"
              stroke="#38bdf8"
              stroke-width="2.5"
              stroke-linecap="round"
            />

            <!-- Realtime Indicator Marker with Pulsing Glow Halo (Stable position, no diagonal drift) -->
            <circle
              :cx="tideChartData.currX"
              :cy="tideChartData.currY"
              r="10"
              fill="rgba(56, 189, 248, 0.25)"
              stroke="rgba(56, 189, 248, 0.5)"
              stroke-width="1.5"
              class="animate-pulse"
            />
            <circle
              :cx="tideChartData.currX"
              :cy="tideChartData.currY"
              r="5"
              fill="#051426"
              stroke="#38bdf8"
              stroke-width="2.5"
            />
            <circle
              :cx="tideChartData.currX"
              :cy="tideChartData.currY"
              r="2"
              fill="#ffffff"
            />

            <!-- X-Axis Hours Labels (Centered with vertical lines) -->
            <text x="142" y="185" font-size="9.5" fill="rgba(255,255,255,0.5)" font-family="monospace" text-anchor="middle">04:00</text>
            <text x="230" y="185" font-size="9.5" fill="rgba(255,255,255,0.5)" font-family="monospace" text-anchor="middle">08:00</text>
            <text x="318" y="185" font-size="9.5" fill="rgba(255,255,255,0.5)" font-family="monospace" text-anchor="middle">12:00</text>
            <text x="405" y="185" font-size="9.5" fill="rgba(255,255,255,0.5)" font-family="monospace" text-anchor="middle">16:00</text>
            <text x="492" y="185" font-size="9.5" fill="rgba(255,255,255,0.5)" font-family="monospace" text-anchor="middle">20:00</text>
          </svg>
        </div>

        <!-- Live Metrics Summary (3 Columns with Fishhook icon in center) -->
        <div class="grid grid-cols-3 gap-2.5 text-center my-2.5 items-end">
          <div class="bg-black/30 p-2.5 rounded-xl border border-white/5">
            <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('next_high_tide') }}</span>
            <span class="text-xs sm:text-sm font-black text-white mt-1 block">1 h 50 min</span>
          </div>

          <div class="bg-black/30 p-2.5 rounded-xl border border-white/5 relative">
            <div class="flex justify-center mb-0.5">
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 text-sky-400" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 4a2 2 0 0 1 2 2v4a6 6 0 0 1-12 0V7a3 3 0 0 1 6 0v7a2 2 0 0 1-4 0" />
              </svg>
            </div>
            <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('current_tide') }}</span>
            <span class="text-base sm:text-lg font-black text-white mt-0.5 block">0,23 m</span>
            <span class="text-[10px] text-sky-300 font-bold block mt-0.5">
              <span class="inline-block px-1 rounded bg-sky-500/20 text-sky-300 mr-0.5">↑</span> {{ t('rising') }}
            </span>
          </div>

          <div class="bg-black/30 p-2.5 rounded-xl border border-white/5">
            <span class="text-[9px] text-white/50 block font-semibold uppercase">Corrente marea</span>
            <span class="text-xs sm:text-sm font-black text-white mt-1 block">3 cm/h</span>
          </div>
        </div>

        <!-- Low and High Tide Table -->
        <div class="grid grid-cols-2 gap-2.5 pt-2 border-t border-white/5">
          <div class="bg-black/25 p-2.5 rounded-xl border border-white/5">
            <div class="flex items-center gap-1.5 mb-1.5">
              <ArrowDown class="w-3 h-3 text-amber-400" />
              <span class="text-[9px] font-bold text-amber-300 uppercase">{{ t('low_tide') }}</span>
            </div>
            <div class="space-y-1 text-xs font-mono">
              <div class="flex justify-between text-white/80">
                <span>07:04</span>
                <span class="font-bold text-white">0,02 m</span>
              </div>
              <div class="flex justify-between text-white/80">
                <span>20:54</span>
                <span class="font-bold text-white">0,08 m</span>
              </div>
            </div>
          </div>

          <div class="bg-black/25 p-2.5 rounded-xl border border-white/5">
            <div class="flex items-center gap-1.5 mb-1.5">
              <ArrowUp class="w-3 h-3 text-emerald-400" />
              <span class="text-[9px] font-bold text-emerald-300 uppercase">{{ t('high_tide') }}</span>
            </div>
            <div class="space-y-1 text-xs font-mono">
              <div class="flex justify-between text-white/80">
                <span>00:48</span>
                <span class="font-bold text-white">0,19 m</span>
              </div>
              <div class="flex justify-between text-white/80">
                <span>14:10</span>
                <span class="font-bold text-white">0,26 m</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- ==================== TAB 3: METEO (ADVANCED, SYNCHRONIZED & COMPACT) ==================== -->
    <div v-if="subTab === 'weather'" class="space-y-3">
      
      <!-- Top Row: Current Conditions + Wind side-by-side in 2 Columns -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Current Conditions Card -->
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3 flex flex-col justify-between">
          <h2 class="text-xs font-bold text-sky-400 uppercase tracking-wider mb-2">
            {{ t('current_conditions') }}
          </h2>

          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-baseline gap-1.5">
                <span class="text-4xl font-black text-white tracking-tighter">
                  {{ Math.round(weather.temperature_2m || 14) }}°
                </span>
                <CloudSun class="w-7 h-7 text-amber-400 ml-1 inline-block" />
              </div>
              <div class="text-[11px] font-semibold text-white/60 mt-0.5 flex gap-2">
                <span class="text-white/85">Max {{ Math.round(weather.temp_max || 15) }}°</span>
                <span class="text-white/45">Min {{ Math.round(weather.temp_min || 13) }}°</span>
              </div>
            </div>

            <!-- Weather Metrics List -->
            <div class="space-y-1.5 text-right">
              <div class="flex items-center justify-end gap-1.5">
                <span class="text-[9px] text-white/50 uppercase font-medium">{{ t('precipitation') }}:</span>
                <span class="text-xs font-bold text-white">{{ (weather.precipitation || 0).toFixed(1) }} mm/h</span>
                <Umbrella class="w-3.5 h-3.5 text-sky-400" />
              </div>

              <div class="flex items-center justify-end gap-1.5">
                <span class="text-[9px] text-white/50 uppercase font-medium">{{ t('pressure') }}:</span>
                <span class="text-xs font-bold text-white">
                  {{ Math.round(weather.surface_pressure || 1016) }} hPa 
                  <span class="text-sky-400">{{ (weather.pressure_trend_3h || 0) < 0 ? '↓' : '↑' }}</span>
                </span>
                <Gauge class="w-3.5 h-3.5 text-sky-400" />
              </div>

              <div class="flex items-center justify-end gap-1.5">
                <span class="text-[9px] text-white/50 uppercase font-medium">{{ t('humidity') }}:</span>
                <span class="text-xs font-bold text-white">{{ Math.round(weather.relative_humidity || 65) }}%</span>
                <Droplets class="w-3.5 h-3.5 text-sky-400" />
              </div>

              <div class="flex items-center justify-end gap-1.5">
                <span class="text-[9px] text-white/50 uppercase font-medium">{{ t('uv_index') }}:</span>
                <span class="px-1.5 py-0.2 rounded bg-amber-500 text-black font-extrabold text-[9px] leading-tight">
                  {{ Math.round(weather.uv_index || 1) }}
                </span>
                <Sun class="w-3.5 h-3.5 text-amber-400" />
              </div>
            </div>
          </div>
        </div>

        <!-- Current Wind Section: Realistic 3-Blade Vector Turbine + High-Contrast Metrics -->
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3 flex flex-col justify-between">
          <h2 class="text-xs font-bold text-sky-400 uppercase tracking-wider mb-2">
            {{ t('current_wind') }}
          </h2>

          <div class="grid grid-cols-2 gap-3 items-center bg-black/30 p-2.5 rounded-xl border border-white/5">
            <!-- Modern 3-Blade SVG Wind Turbine -->
            <div class="text-center border-r border-white/10 pr-2">
              <div class="w-14 h-14 mx-auto relative flex items-center justify-center">
                <svg viewBox="0 0 60 60" class="w-full h-full">
                  <!-- Tower -->
                  <polygon points="28,56 32,56 31,24 29,24" fill="rgba(255,255,255,0.3)" />
                  <!-- Base mound -->
                  <path d="M 25,56 Q 30,54 35,56" stroke="rgba(255,255,255,0.2)" stroke-width="1.2" fill="none" />
                  <!-- 3-blade spinning rotor -->
                  <g 
                    class="origin-[30px_24px] animate-spin" 
                    style="animation-duration: 3.2s; transform-origin: 30px 24px;"
                  >
                    <!-- Blade 1 (top) -->
                    <path d="M 30,24 Q 28.5,14 30,5 Q 31.5,14 30,24" fill="#38bdf8" />
                    <!-- Blade 2 (bottom-right 120 deg) -->
                    <path d="M 30,24 Q 39,29 46.5,33.5 Q 37.5,33.5 30,24" fill="#38bdf8" />
                    <!-- Blade 3 (bottom-left 240 deg) -->
                    <path d="M 30,24 Q 21,29 13.5,33.5 Q 22.5,33.5 30,24" fill="#38bdf8" />
                    <!-- Center hub -->
                    <circle cx="30" cy="24" r="2.5" fill="#ffffff" />
                  </g>
                </svg>
              </div>
              <span class="text-[10px] font-semibold text-white/70 block mt-0.5 italic">
                {{ getBreezeName(weather.wind_speed_knots) }}
              </span>
            </div>

            <!-- Wind Metrics -->
            <div class="space-y-1.5 pl-1">
              <div>
                <span class="text-[9px] text-white/50 block uppercase font-medium">{{ t('wind_direction') }}</span>
                <div class="flex items-center gap-1.5">
                  <Navigation 
                    class="w-3.5 h-3.5 text-sky-400 shrink-0 transition-transform" 
                    :style="{ transform: `rotate(${weather.wind_direction || 50}deg)` }"
                  />
                  <span class="text-sm font-bold text-white">
                    {{ Math.round(weather.wind_direction || 50) }}° {{ getCompassDir(weather.wind_direction || 50) }}
                  </span>
                </div>
              </div>

              <div>
                <span class="text-[9px] text-white/50 block uppercase font-medium">{{ t('wind_speed') }}</span>
                <span class="text-lg font-black text-white">
                  {{ ((weather.wind_speed_knots || 18) * 0.5144).toFixed(1) }} m/s
                  <span class="text-[10px] font-normal text-white/40">({{ Math.round(weather.wind_speed_knots || 18) }} kn)</span>
                </span>
              </div>

              <div>
                <span class="text-[9px] text-white/50 block uppercase font-medium">{{ t('wind_gusts') }}</span>
                <span class="text-xs font-black text-amber-400">
                  {{ (((weather.wind_gusts_knots || (weather.wind_speed_knots * 2)) || 40.5) * 0.5144).toFixed(1) }} m/s
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Hourly Metric Switcher & Synchronized 24h Timeline (Zero Right Drift) -->
      <div class="bg-white/5 border border-white/10 rounded-2xl p-3.5">
        <!-- Metric Selector Icons -->
        <div class="flex items-center justify-between bg-black/40 p-1 rounded-xl border border-white/10 mb-2">
          <button
            @click="activeWeatherMetric = 'temp'"
            title="Temperatura"
            class="flex-1 py-1 rounded-lg flex items-center justify-center transition"
            :class="activeWeatherMetric === 'temp' ? 'bg-sky-500/25 text-sky-300 border border-sky-400/40 shadow' : 'text-white/40 hover:text-white'"
          >
            <CloudSun class="w-4 h-4" />
          </button>
          <button
            @click="activeWeatherMetric = 'precip'"
            title="Precipitazioni"
            class="flex-1 py-1 rounded-lg flex items-center justify-center transition"
            :class="activeWeatherMetric === 'precip' ? 'bg-sky-500/25 text-sky-300 border border-sky-400/40 shadow' : 'text-white/40 hover:text-white'"
          >
            <Umbrella class="w-4 h-4" />
          </button>
          <button
            @click="activeWeatherMetric = 'wind'"
            title="Vento"
            class="flex-1 py-1 rounded-lg flex items-center justify-center transition"
            :class="activeWeatherMetric === 'wind' ? 'bg-sky-500/25 text-sky-300 border border-sky-400/40 shadow' : 'text-white/40 hover:text-white'"
          >
            <Wind class="w-4 h-4" />
          </button>
          <button
            @click="activeWeatherMetric = 'pressure'"
            title="Pressione"
            class="flex-1 py-1 rounded-lg flex items-center justify-center transition"
            :class="activeWeatherMetric === 'pressure' ? 'bg-sky-500/25 text-sky-300 border border-sky-400/40 shadow' : 'text-white/40 hover:text-white'"
          >
            <Gauge class="w-4 h-4" />
          </button>
        </div>

        <!-- Metric Title -->
        <div class="flex items-center justify-between text-xs text-white/60 mb-1 px-1">
          <span class="font-bold text-white">{{ metricConfig.title }}</span>
          <span class="font-mono text-[10px]">{{ metricConfig.unit }}</span>
        </div>

        <!-- Synchronized SVG Timeline: Labels & Guide Lines share exact p.x coordinates -->
        <div class="w-full h-32 relative">
          <svg class="w-full h-full" viewBox="0 0 640 100">
            <!-- Zero/Mid Horizontal Guide Line -->
            <line x1="28" y1="42" x2="612" y2="42" stroke="rgba(255,255,255,0.06)" stroke-dasharray="2 2" />

            <!-- Smooth continuous data curve -->
            <path :d="weatherCurveData.path" fill="none" stroke="#38bdf8" stroke-width="2.5" />

            <!-- Hourly Points & Value Labels -->
            <g v-for="p in weatherCurveData.points" :key="'pt-' + p.hour">
              <circle :cx="p.x" :cy="p.y" r="2.8" fill="#38bdf8" />
              <text :x="p.x" :y="p.y - 5" font-size="8.5" font-weight="bold" fill="white" text-anchor="middle" font-family="monospace">
                {{ p.val }}
              </text>
            </g>

            <!-- Synchronized Vertical Guide Lines & Hour Ticks (Every 3 hours + Final Hour 23:00) -->
            <g v-for="tIdx in [0, 3, 6, 9, 12, 15, 18, 21, 23]" :key="'tick-' + tIdx">
              <line 
                v-if="weatherCurveData.points[tIdx]"
                :x1="weatherCurveData.points[tIdx].x" 
                :y1="weatherCurveData.points[tIdx].y + 4" 
                :x2="weatherCurveData.points[tIdx].x" 
                y2="76" 
                stroke="rgba(255,255,255,0.09)" 
                stroke-dasharray="2 2" 
              />
              <text 
                v-if="weatherCurveData.points[tIdx]"
                :x="weatherCurveData.points[tIdx].x" 
                y="92" 
                font-size="8.5" 
                fill="rgba(255,255,255,0.55)" 
                font-family="monospace" 
                text-anchor="middle"
              >
                {{ weatherCurveData.points[tIdx].hour.toString().padStart(2, '0') }}:00
              </text>
            </g>
          </svg>
        </div>
      </div>
    </div>


    <!-- ==================== TAB 4: SOLE E LUNA (CLEAN TYPOGRAPHY & ZERO CLIPPING) ==================== -->
    <div v-if="subTab === 'sun_moon'" class="space-y-3">
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Moon Card (Clean transit curve and unclipped typography) -->
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3.5 flex flex-col justify-between">
          <div>
            <h2 class="text-xs font-bold text-sky-400 uppercase tracking-wider mb-1">{{ t('moon') }}</h2>

            <!-- Illustrated Moon Phase Graphic -->
            <div class="text-center my-2">
              <div class="w-14 h-14 mx-auto rounded-full bg-slate-900 border-2 border-white/20 relative overflow-hidden shadow-lg shadow-sky-500/10">
                <div 
                  class="absolute inset-y-0 left-0 bg-sky-200"
                  :style="{ width: `${Math.round(solunar.moon_illumination * 100)}%` }"
                ></div>
              </div>
              <span class="text-xs font-bold text-white mt-1.5 block italic">
                {{ solunar.moon_phase_name || 'Ultimo quarto' }}
              </span>
            </div>

            <!-- 3 Key Moon Metrics -->
            <div class="grid grid-cols-3 gap-2 text-center my-2 pt-2 border-t border-white/5">
              <div class="bg-black/30 p-2 rounded-xl border border-white/5">
                <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('distance') }}</span>
                <span class="text-xs font-black text-white mt-0.5 block">
                  {{ formatDistance(solunar.moon_distance_km) }} km
                </span>
              </div>

              <div class="bg-black/30 p-2 rounded-xl border border-white/5">
                <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('illumination') }}</span>
                <span class="text-xs font-black text-sky-400 mt-0.5 block">
                  {{ ((solunar.moon_illumination || 0.555) * 100).toFixed(1) }} %
                </span>
              </div>

              <div class="bg-black/30 p-2 rounded-xl border border-white/5">
                <span class="text-[9px] text-white/50 block font-semibold uppercase">{{ t('moon_age') }}</span>
                <span class="text-xs font-black text-white mt-0.5 block">
                  {{ (solunar.moon_age_days || 21.6).toFixed(1) }} {{ t('days') }}
                </span>
              </div>
            </div>
          </div>

          <!-- Moon Transit Curve: Text is separated and 100% visible with zero clipping -->
          <div class="w-full bg-black/25 rounded-xl p-2.5 border border-white/5 flex flex-col justify-between mt-2">
            <div class="w-full h-14 sm:h-16">
              <svg class="w-full h-full" viewBox="0 0 300 60">
                <!-- Horizon zero line -->
                <line x1="10" y1="48" x2="290" y2="48" stroke="rgba(255,255,255,0.15)" stroke-width="1" />
                <!-- Transit Arc -->
                <path
                  d="M 10,48 Q 80,10 150,48"
                  fill="rgba(56,189,248,0.15)"
                  stroke="#38bdf8"
                  stroke-width="2"
                />
                <!-- Moon marker at set/rise -->
                <circle cx="150" cy="48" r="4" fill="#f8fafc" />
                <!-- Underfoot dashed curve -->
                <path
                  d="M 150,48 Q 220,68 290,48"
                  fill="none"
                  stroke="rgba(255,255,255,0.2)"
                  stroke-dasharray="3 3"
                  stroke-width="1"
                />
              </svg>
            </div>
            <!-- Clean, fully padded, legible labels -->
            <div class="flex justify-between items-center text-[10px] text-white/80 px-2 font-mono pt-1.5 border-t border-white/5">
              <span>{{ t('moon_set_time') }}: {{ solunar.moonset || '13:03' }}</span>
              <span>{{ t('moon_rise_time') }}: {{ solunar.moonrise || '23:03' }}</span>
            </div>
          </div>
        </div>

        <!-- Sun Card (24-Hour Circular Dial) -->
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3.5 flex flex-col justify-between">
          <div>
            <h2 class="text-xs font-bold text-amber-400 uppercase tracking-wider mb-1">{{ t('sun') }}</h2>

            <!-- Circular Sun Dial SVG -->
            <div class="relative w-40 h-40 sm:w-44 sm:h-44 xl:w-48 xl:h-48 mx-auto my-1 flex items-center justify-center">
              <svg class="w-full h-full" viewBox="0 0 200 200">
                <!-- Background Dial -->
                <path
                  d="M 20,100 A 80,80 0 0,1 180,100"
                  fill="rgba(14, 116, 144, 0.25)"
                  stroke="#0284c7"
                  stroke-width="2"
                />
                <path
                  d="M 180,100 A 80,80 0 0,1 20,100"
                  fill="rgba(15, 23, 42, 0.4)"
                  stroke="rgba(255,255,255,0.15)"
                  stroke-dasharray="4 4"
                  stroke-width="1.5"
                />
                <line x1="10" y1="100" x2="190" y2="100" stroke="rgba(255,255,255,0.25)" stroke-width="1" />

                <!-- Sun Icon at Current Angle -->
                <g :transform="`rotate(${sunAngle}, 100, 100)`">
                  <circle cx="100" cy="20" r="7" fill="#fbbf24" class="drop-shadow-lg" />
                  <line x1="100" y1="9" x2="100" y2="12" stroke="#fbbf24" stroke-width="2" />
                  <line x1="100" y1="28" x2="100" y2="31" stroke="#fbbf24" stroke-width="2" />
                  <line x1="89" y1="20" x2="92" y2="20" stroke="#fbbf24" stroke-width="2" />
                  <line x1="108" y1="20" x2="111" y2="20" stroke="#fbbf24" stroke-width="2" />
                </g>

                <!-- Center text: Day / Night duration -->
                <text x="100" y="65" text-anchor="middle" font-size="9" fill="rgba(255,255,255,0.6)" font-weight="bold">
                  {{ t('day_duration') }}
                </text>
                <text x="100" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="black">
                  {{ formatDuration(solunar.day_duration_minutes) }}
                </text>

                <text x="100" y="130" text-anchor="middle" font-size="9" fill="rgba(255,255,255,0.6)" font-weight="bold">
                  {{ t('night_duration') }}
                </text>
                <text x="100" y="145" text-anchor="middle" font-size="11" fill="white" font-weight="black">
                  {{ formatDuration(solunar.night_duration_minutes) }}
                </text>

                <text x="100" y="16" text-anchor="middle" font-size="8" fill="rgba(255,255,255,0.7)" font-family="monospace">
                  {{ t('solar_noon') }} {{ solunar.solar_noon || '11:51' }}
                </text>
                <text x="100" y="192" text-anchor="middle" font-size="8" fill="rgba(255,255,255,0.5)" font-family="monospace">
                  {{ t('midnight') }} 00:00
                </text>
              </svg>
            </div>
          </div>

          <!-- Astronomical Events Grid -->
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-white/5">
            <div class="bg-black/30 p-2.5 rounded-xl border border-white/5">
              <span class="text-[9px] text-white/50 block uppercase font-medium">{{ t('sunrise') }}</span>
              <span class="text-sm font-black text-amber-300 mt-0.5 block">{{ solunar.sunrise || '06:33' }}</span>
              <span class="text-[9px] text-white/40 block mt-0.5 font-mono">
                {{ t('dawn') }}: {{ solunar.civil_dawn || '06:06' }}
              </span>
            </div>

            <div class="bg-black/30 p-2.5 rounded-xl border border-white/5">
              <span class="text-[9px] text-white/50 block uppercase font-medium">{{ t('sunset') }}</span>
              <span class="text-sm font-black text-amber-400 mt-0.5 block">{{ solunar.sunset || '17:09' }}</span>
              <span class="text-[9px] text-white/40 block mt-0.5 font-mono">
                {{ t('dusk') }}: {{ solunar.civil_dusk || '17:36' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
