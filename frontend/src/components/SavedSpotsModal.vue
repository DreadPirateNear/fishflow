<script setup>
import { ref } from 'vue'
import { Star, Trash2, MapPin, X, Plus, Navigation } from 'lucide-vue-next'
import { t } from '../i18n/index.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  embedded: {
    type: Boolean,
    default: false
  },
  savedSpots: {
    type: Array,
    default: () => []
  },
  currentLocation: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'selectSpot', 'deleteSpot', 'saveCurrentSpot'])

const spotNameInput = ref('')

const handleSave = () => {
  const name = spotNameInput.value.trim() || props.currentLocation.name || 'Mio Spot'
  emit('saveCurrentSpot', {
    id: Date.now().toString(),
    name,
    lat: props.currentLocation.lat,
    lon: props.currentLocation.lon,
    isMarine: props.currentLocation.isMarine !== false
  })
  spotNameInput.value = ''
}
</script>

<template>
  <!-- Embedded Mode (Inside Spots Tab View) -->
  <div v-if="embedded" class="w-full flex-1 flex flex-col p-4 sm:p-6 overflow-y-auto">
    <!-- Add Current Spot Form -->
    <div class="mb-5 p-4 rounded-2xl bg-white/5 border border-white/10">
      <span class="text-xs font-semibold text-white/80 block mb-2">{{ t('save_spot') }}:</span>
      <div class="flex flex-col sm:flex-row gap-2">
        <input 
          v-model="spotNameInput"
          type="text"
          :placeholder="currentLocation.name || 'Nome dello spot...'"
          class="flex-1 bg-black/40 border border-white/15 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-white/40 focus:outline-none focus:border-sky-400"
        />
        <button 
          @click="handleSave"
          class="px-4 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 active:scale-95 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition shadow-lg shadow-sky-500/20"
        >
          <Plus class="w-4 h-4" />
          {{ t('save_spot') }}
        </button>
      </div>
    </div>

    <!-- Saved Spots Grid on Desktop / List on Mobile -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="s in savedSpots"
        :key="s.id"
        class="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/10 hover:border-sky-400/40 hover:bg-white/[0.08] transition group shadow-sm"
      >
        <button 
          @click="emit('selectSpot', s)"
          class="flex items-center gap-3 text-left flex-1 truncate"
        >
          <div class="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-400/20 flex items-center justify-center text-sky-400 shrink-0 group-hover:scale-105 transition">
            <MapPin class="w-4 h-4" />
          </div>
          <div class="truncate">
            <span class="text-sm font-semibold text-white block truncate">{{ s.name }}</span>
            <span class="text-[10px] text-white/50 block font-mono">{{ s.lat.toFixed(4) }}, {{ s.lon.toFixed(4) }}</span>
          </div>
        </button>

        <button 
          @click="emit('deleteSpot', s.id)"
          :title="t('remove_spot')"
          class="p-2 text-white/30 hover:text-red-400 transition"
        >
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>

    <div v-if="!savedSpots.length" class="text-center py-12 text-white/40 text-xs">
      Nessuno spot salvato ancora. Clicca su "Salva" per memorizzare il tuo spot preferito!
    </div>
  </div>

  <!-- Modal Dialog Mode -->
  <div 
    v-else-if="isOpen"
    class="fixed inset-0 z-[1000] bg-black/75 backdrop-blur-sm flex flex-col justify-end sm:justify-center items-center p-0 sm:p-4 animate-in fade-in"
  >
    <div class="bg-[#071a33] border border-white/10 w-full sm:max-w-md rounded-t-3xl sm:rounded-3xl p-5 shadow-2xl flex flex-col max-h-[85vh]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-white/10">
        <div class="flex items-center gap-2">
          <Star class="w-5 h-5 text-amber-400 fill-amber-400" />
          <h2 class="text-lg font-bold text-white">{{ t('favorites') }}</h2>
        </div>
        <button @click="emit('close')" class="p-1 rounded-full text-white/50 hover:text-white transition">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Add Current Spot Form -->
      <div class="my-4 p-3 rounded-2xl bg-white/5 border border-white/10">
        <span class="text-xs font-semibold text-white/80 block mb-2">{{ t('save_spot') }}:</span>
        <div class="flex gap-2">
          <input 
            v-model="spotNameInput"
            type="text"
            :placeholder="currentLocation.name || 'Nome dello spot...'"
            class="flex-1 bg-black/30 border border-white/15 rounded-xl px-3 py-2 text-xs text-white placeholder-white/40 focus:outline-none focus:border-sky-400"
          />
          <button 
            @click="handleSave"
            class="px-3.5 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 active:scale-95 text-white font-bold text-xs flex items-center gap-1 transition"
          >
            <Plus class="w-4 h-4" />
            Salva
          </button>
        </div>
      </div>

      <!-- Saved Spots List -->
      <div class="flex-1 overflow-y-auto space-y-2 no-scrollbar">
        <div
          v-for="s in savedSpots"
          :key="s.id"
          class="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/20 transition group"
        >
          <button 
            @click="emit('selectSpot', s); emit('close')"
            class="flex items-center gap-3 text-left flex-1 truncate"
          >
            <MapPin class="w-4 h-4 text-sky-400 shrink-0" />
            <div class="truncate">
              <span class="text-sm font-semibold text-white block">{{ s.name }}</span>
              <span class="text-[10px] text-white/50 block font-mono">{{ s.lat.toFixed(4) }}, {{ s.lon.toFixed(4) }}</span>
            </div>
          </button>

          <button 
            @click="emit('deleteSpot', s.id)"
            :title="t('remove_spot')"
            class="p-2 text-white/30 hover:text-red-400 transition"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>

        <div v-if="!savedSpots.length" class="text-center py-8 text-white/40 text-xs">
          Nessuno spot salvato ancora. Clicca su "Salva" per memorizzare il tuo spot preferito!
        </div>
      </div>
    </div>
  </div>
</template>
