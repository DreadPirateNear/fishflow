<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { Search, MapPin, X, Loader2, Navigation } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'selectLocation', 'useGps'])

const query = ref('')
const results = ref([])
const loading = ref(false)
let debounceTimer = null

const handleInput = () => {
  clearTimeout(debounceTimer)
  if (!query.value.trim()) {
    results.value = []
    return
  }
  debounceTimer = setTimeout(async () => {
    loading.value = true
    try {
      const res = await axios.get('/api/v1/search', {
        params: { q: query.value.trim() }
      })
      results.value = res.data
    } catch (e) {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 350)
}

const select = (item) => {
  emit('selectLocation', {
    name: item.name,
    lat: item.latitude,
    lon: item.longitude,
    isMarine: item.is_marine
  })
  emit('close')
}
</script>

<template>
  <div 
    v-if="isOpen"
    class="fixed inset-0 z-[1000] bg-black/75 backdrop-blur-sm flex flex-col justify-end sm:justify-center items-center p-0 sm:p-4 animate-in fade-in"
  >
    <div class="bg-ocean-900 border border-white/10 w-full sm:max-w-md rounded-t-3xl sm:rounded-3xl p-5 shadow-2xl flex flex-col max-h-[85vh]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-white/10">
        <h2 class="text-lg font-bold text-white">Cerca Spot o Località</h2>
        <button @click="emit('close')" class="p-1 rounded-full text-white/50 hover:text-white transition">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Search Input -->
      <div class="relative my-4">
        <Search class="absolute left-3.5 top-3 w-4 h-4 text-white/40" />
        <input
          v-model="query"
          @input="handleInput"
          type="text"
          placeholder="Es: Venezia, Lago di Garda, Livorno..."
          autofocus
          class="w-full bg-white/5 border border-white/15 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white placeholder-white/40 focus:outline-none focus:border-sky-400 transition"
        />
        <Loader2 v-if="loading" class="absolute right-3.5 top-3 w-4 h-4 text-sky-400 animate-spin" />
      </div>

      <!-- GPS Quick Button -->
      <button
        @click="emit('useGps'); emit('close')"
        class="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-sky-500/20 text-sky-300 border border-sky-400/30 text-xs font-semibold hover:bg-sky-500/30 active:scale-98 transition mb-3"
      >
        <Navigation class="w-4 h-4" />
        Usa Posizione GPS Attuale
      </button>

      <!-- Results List -->
      <div class="flex-1 overflow-y-auto space-y-1.5 no-scrollbar">
        <button
          v-for="(r, idx) in results"
          :key="idx"
          @click="select(r)"
          class="w-full flex items-start gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition text-left border border-white/5"
        >
          <MapPin class="w-4 h-4 text-sky-400 mt-0.5 shrink-0" />
          <div class="truncate">
            <span class="text-sm font-semibold text-white block">{{ r.name }}</span>
            <span class="text-[11px] text-white/50 block truncate">{{ r.display_name }}</span>
          </div>
        </button>

        <p v-if="!loading && query && !results.length" class="text-center text-xs text-white/40 py-6">
          Nessuna località trovata per "{{ query }}"
        </p>
      </div>
    </div>
  </div>
</template>
