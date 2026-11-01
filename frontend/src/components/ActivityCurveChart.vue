<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { Sparkles } from 'lucide-vue-next'
import { t } from '../i18n/index.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
)

const props = defineProps({
  hourlyData: {
    type: Array,
    default: () => []
  },
  solunar: {
    type: Object,
    default: () => ({})
  },
  isToday: {
    type: Boolean,
    default: true
  }
})

// Custom plugin to draw the live time vertical indicator and cyan glowing marker
const currentHourPlugin = {
  id: 'currentHourIndicator',
  afterDatasetsDraw(chart) {
    if (!props.isToday || !props.hourlyData.length) return
    const now = new Date()
    const currentHour = now.getHours() + (now.getMinutes() / 60)
    
    const meta = chart.getDatasetMeta(0)
    if (!meta.data || meta.data.length < 24) return

    // Interpolate pixel position for current fractional hour
    const hFloor = Math.min(23, Math.floor(currentHour))
    const hCeil = Math.min(23, Math.ceil(currentHour))
    const ratio = currentHour - hFloor

    const pt1 = meta.data[hFloor]
    const pt2 = meta.data[hCeil]

    if (!pt1 || !pt2) return

    const x = pt1.x + (pt2.x - pt1.x) * ratio
    const y = pt1.y + (pt2.y - pt1.y) * ratio

    const ctx = chart.ctx
    const yAxis = chart.scales.y
    ctx.save()

    // Draw vertical dotted guide line to current hour
    ctx.beginPath()
    ctx.setLineDash([3, 3])
    ctx.moveTo(x, yAxis.top)
    ctx.lineTo(x, yAxis.bottom)
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)'
    ctx.lineWidth = 1.5
    ctx.stroke()
    ctx.setLineDash([])

    // Outer cyan glow aura
    ctx.beginPath()
    ctx.arc(x, y, 8, 0, 2 * Math.PI)
    ctx.fillStyle = 'rgba(56, 189, 248, 0.25)'
    ctx.fill()

    // White outer ring
    ctx.beginPath()
    ctx.arc(x, y, 5, 0, 2 * Math.PI)
    ctx.fillStyle = '#ffffff'
    ctx.fill()

    // Inner bright cyan center
    ctx.beginPath()
    ctx.arc(x, y, 3, 0, 2 * Math.PI)
    ctx.fillStyle = '#06b6d4'
    ctx.fill()

    ctx.restore()
  }
}

const chartData = computed(() => {
  const labels = props.hourlyData.map(h => `${String(h.hour).padStart(2, '0')}:00`)
  const scores = props.hourlyData.map(h => h.score)

  return {
    labels,
    datasets: [
      {
        label: 'Attività Pesca',
        data: scores,
        borderColor: '#38bdf8',
        borderWidth: 2.5,
        tension: 0.42,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#10b981',
        pointHoverBorderColor: '#ffffff',
        fill: 'origin',
        backgroundColor: (context) => {
          const ctx = context.chart.ctx
          const gradient = ctx.createLinearGradient(0, 0, 0, 160)
          gradient.addColorStop(0, 'rgba(56, 189, 248, 0.35)')
          gradient.addColorStop(0.7, 'rgba(2, 132, 199, 0.08)')
          gradient.addColorStop(1, 'rgba(2, 132, 199, 0.0)')
          return gradient
        }
      }
    ]
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(3, 11, 20, 0.95)',
      titleColor: '#ffffff',
      bodyColor: '#38bdf8',
      borderColor: 'rgba(255, 255, 255, 0.15)',
      borderWidth: 1,
      padding: 10,
      displayColors: false,
      callbacks: {
        title: (items) => `Ore ${items[0]?.label || ''}`,
        label: (item) => `Indice Solunare: ${item.raw}/100`
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: (ctx) => {
          const hour = ctx.index
          if ([4, 8, 12, 16, 20].includes(hour)) {
            return 'rgba(255, 255, 255, 0.08)'
          }
          return 'transparent'
        },
        drawBorder: false
      },
      ticks: {
        color: 'rgba(255, 255, 255, 0.5)',
        font: {
          size: 9.5,
          family: 'monospace'
        },
        callback: function (val, index) {
          const hoursToShow = [0, 4, 8, 12, 16, 20]
          return hoursToShow.includes(index) ? `${String(index).padStart(2, '0')}:00` : ''
        },
        autoSkip: false,
        maxRotation: 0
      }
    },
    y: {
      min: 0,
      max: 100,
      grid: {
        color: 'rgba(255, 255, 255, 0.05)',
        drawBorder: false
      },
      ticks: {
        color: 'rgba(255, 255, 255, 0.35)',
        font: {
          size: 8.5
        },
        stepSize: 25,
        callback: (value) => {
          if (value === 75) return 'ALTA'
          if (value === 45) return 'MEDIA'
          if (value === 15) return 'BASSA'
          return ''
        }
      }
    }
  }
}))

// Major and Minor Windows
const majorWindows = computed(() => props.solunar?.major_windows || [])
const minorWindows = computed(() => props.solunar?.minor_windows || [])
</script>

<template>
  <div class="flex flex-col gap-3 relative px-1 select-none">
    <!-- Chart Container -->
    <div class="h-32 sm:h-36 xl:h-40 w-full relative">
      <Line :data="chartData" :options="chartOptions" :plugins="[currentHourPlugin]" />
    </div>

    <!-- Solunar Times Table (2 Columns) -->
    <div class="grid grid-cols-2 gap-2.5 pt-2 border-t border-white/10 select-none">
      <!-- Major Times -->
      <div class="bg-black/30 p-2.5 rounded-2xl border border-white/5">
        <div class="flex items-center gap-1.5 mb-1.5">
          <Sparkles class="w-3.5 h-3.5 text-cyan-400" />
          <h3 class="text-[10px] font-bold text-cyan-300 tracking-wider uppercase">
            {{ t('major_times') }}
          </h3>
        </div>
        <div class="space-y-1">
          <p 
            v-for="(w, idx) in majorWindows" 
            :key="idx" 
            class="text-xs font-semibold text-white/95 tracking-wide"
          >
            {{ w.start }} &mdash; {{ w.end }}
          </p>
          <p v-if="!majorWindows.length" class="text-xs text-white/40">--:-- &mdash; --:--</p>
        </div>
      </div>

      <!-- Minor Times -->
      <div class="bg-black/30 p-2.5 rounded-2xl border border-white/5">
        <div class="flex items-center gap-1.5 mb-1.5">
          <Sparkles class="w-3.5 h-3.5 text-teal-400" />
          <h3 class="text-[10px] font-bold text-teal-300 tracking-wider uppercase">
            {{ t('minor_times') }}
          </h3>
        </div>
        <div class="space-y-1">
          <p 
            v-for="(w, idx) in minorWindows" 
            :key="idx" 
            class="text-xs font-semibold text-white/95 tracking-wide"
          >
            {{ w.start }} &mdash; {{ w.end }}
          </p>
          <p v-if="!minorWindows.length" class="text-xs text-white/40">--:-- &mdash; --:--</p>
        </div>
      </div>
    </div>
  </div>
</template>
