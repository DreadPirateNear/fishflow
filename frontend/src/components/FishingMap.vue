<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import axios from 'axios'
import { 
  Layers, 
  Navigation, 
  Plus, 
  MapPin, 
  Search, 
  X, 
  Loader2, 
  TrendingUp, 
  Bookmark, 
  Waves,
  Check
} from 'lucide-vue-next'

const props = defineProps({
  currentLocation: {
    type: Object,
    default: () => ({ lat: 44.407, lon: 8.927, name: 'Spot Attivo' })
  },
  savedSpots: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['selectSpot', 'loadSpot', 'addSpot'])

const mapContainer = ref(null)
let map = null
let currentMarker = null
let inspectionMarker = null
let spotMarkersLayer = null
let satelliteLayer = null
let streetLayer = null
const isSatellite = ref(true)

// Heading and Compass
const heading = ref(19)
const bearing = ref(51)

// Search bar state
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const showSearchDropdown = ref(false)
let searchDebounceTimer = null

// Inspected Spot Card state
const inspectedSpot = ref(null)
const loadingReverseGeocode = ref(false)
const spotSavedSuccess = ref(false)

const toggleMapLayer = () => {
  if (!map) return
  if (isSatellite.value) {
    map.removeLayer(satelliteLayer)
    map.addLayer(streetLayer)
    isSatellite.value = false
  } else {
    map.removeLayer(streetLayer)
    map.addLayer(satelliteLayer)
    isSatellite.value = true
  }
}

const centerOnUser = () => {
  if (!map) return
  map.setView([props.currentLocation.lat, props.currentLocation.lon], 15)
}

// Search locations
const handleSearchInput = () => {
  clearTimeout(searchDebounceTimer)
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    showSearchDropdown.value = false
    return
  }

  searchDebounceTimer = setTimeout(async () => {
    isSearching.value = true
    try {
      const res = await axios.get('/api/v1/search', {
        params: { q: searchQuery.value.trim() }
      })
      searchResults.value = res.data
      showSearchDropdown.value = true
    } catch (e) {
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }, 350)
}

const handleSelectSearchResult = (result) => {
  searchQuery.value = ''
  searchResults.value = []
  showSearchDropdown.value = false

  const spot = {
    name: result.name,
    display_name: result.display_name,
    lat: result.latitude,
    lon: result.longitude,
    isMarine: result.is_marine
  }

  inspectCoordinates(spot.lat, spot.lon, spot.name, spot.display_name, spot.isMarine)
  if (map) {
    map.flyTo([spot.lat, spot.lon], 14, { duration: 1.2 })
  }
}

// Inspection Marker & Reverse Geocode
const inspectCoordinates = async (lat, lon, knownName = null, knownDisplayName = null, knownIsMarine = null) => {
  if (!map) return

  const formattedLat = parseFloat(lat.toFixed(4))
  const formattedLon = parseFloat(lon.toFixed(4))

  // Create or update inspection marker
  if (inspectionMarker) {
    inspectionMarker.setLatLng([formattedLat, formattedLon])
  } else {
    const inspectionIcon = L.divIcon({
      className: 'custom-inspection-marker',
      html: `
        <div class="relative w-8 h-8 flex items-center justify-center">
          <div class="absolute w-8 h-8 rounded-full bg-cyan-400/35 animate-ping"></div>
          <div class="w-6 h-6 rounded-full bg-cyan-500 border-2 border-white shadow-xl flex items-center justify-center text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="4"/></svg>
          </div>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    })
    inspectionMarker = L.marker([formattedLat, formattedLon], { icon: inspectionIcon }).addTo(map)
  }

  spotSavedSuccess.value = false

  if (knownName) {
    inspectedSpot.value = {
      name: knownName,
      display_name: knownDisplayName || `Coord: ${formattedLat}, ${formattedLon}`,
      lat: formattedLat,
      lon: formattedLon,
      isMarine: knownIsMarine ?? true
    }
    return
  }

  inspectedSpot.value = {
    name: `Spot (${formattedLat}, ${formattedLon})`,
    display_name: 'Rilevamento località in corso...',
    lat: formattedLat,
    lon: formattedLon,
    isMarine: true
  }

  loadingReverseGeocode.value = true
  try {
    const res = await axios.get('/api/v1/reverse-geocode', {
      params: { lat: formattedLat, lon: formattedLon }
    })
    if (res.data) {
      inspectedSpot.value = {
        name: res.data.name,
        display_name: res.data.display_name,
        lat: formattedLat,
        lon: formattedLon,
        isMarine: res.data.is_marine
      }
    }
  } catch (err) {
    // Keep formatted coordinate fallback
  } finally {
    loadingReverseGeocode.value = false
  }
}

const handleConfirmLoadSpot = () => {
  if (!inspectedSpot.value) return
  emit('loadSpot', { ...inspectedSpot.value })
  inspectedSpot.value = null
  if (inspectionMarker) {
    map.removeLayer(inspectionMarker)
    inspectionMarker = null
  }
}

const handleSaveInspectedSpot = () => {
  if (!inspectedSpot.value) return
  emit('addSpot', {
    id: Date.now().toString(),
    name: inspectedSpot.value.name,
    display_name: inspectedSpot.value.display_name,
    lat: inspectedSpot.value.lat,
    lon: inspectedSpot.value.lon,
    isMarine: inspectedSpot.value.isMarine
  })
  spotSavedSuccess.value = true
  setTimeout(() => {
    spotSavedSuccess.value = false
  }, 2500)
}

const closeInspectedSpot = () => {
  inspectedSpot.value = null
  if (inspectionMarker && map) {
    map.removeLayer(inspectionMarker)
    inspectionMarker = null
  }
}

onMounted(() => {
  if (!mapContainer.value) return

  // Initialize Leaflet map
  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false
  }).setView([props.currentLocation.lat, props.currentLocation.lon], 14)

  // Satellite tile layer: Esri World Imagery
  satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19
  })

  // OpenStreetMap standard layer
  streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}.png', {
    maxZoom: 19
  })

  satelliteLayer.addTo(map)

  // Create custom pulsing user location marker
  const userIcon = L.divIcon({
    className: 'custom-user-marker',
    html: `
      <div class="relative w-6 h-6 flex items-center justify-center">
        <div class="absolute w-6 h-6 rounded-full bg-blue-500/30 animate-ping"></div>
        <div class="w-4 h-4 rounded-full bg-blue-500 border-2 border-white shadow-md"></div>
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  currentMarker = L.marker([props.currentLocation.lat, props.currentLocation.lon], { icon: userIcon }).addTo(map)

  // Spot markers layer
  spotMarkersLayer = L.layerGroup().addTo(map)
  updateSpotMarkers()

  // Click on map to inspect coordinate and load spot
  map.on('click', (e) => {
    showSearchDropdown.value = false
    inspectCoordinates(e.latlng.lat, e.latlng.lng)
  })

  // Handle device orientation for compass if available
  if (window.DeviceOrientationEvent) {
    window.addEventListener('deviceorientation', handleOrientation)
  }
})

const handleOrientation = (event) => {
  if (event.alpha !== null) {
    heading.value = Math.round(event.alpha)
  }
}

const updateSpotMarkers = () => {
  if (!spotMarkersLayer) return
  spotMarkersLayer.clearLayers()

  const spotIcon = L.divIcon({
    className: 'custom-spot-marker',
    html: `
      <div class="w-7 h-7 rounded-full bg-amber-500/90 border-2 border-white flex items-center justify-center shadow-lg text-white">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6.5 12c.94-3.46 4.94-6 8.5-6 3.56 0 6.06 2.54 7 6-.94 3.46-3.44 6-7 6s-7.56-2.54-8.5-6Z"/></svg>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  })

  props.savedSpots.forEach(s => {
    const m = L.marker([s.lat, s.lon], { icon: spotIcon })
    m.on('click', (e) => {
      L.DomEvent.stopPropagation(e)
      inspectCoordinates(s.lat, s.lon, s.name, s.display_name, s.isMarine)
    })
    spotMarkersLayer.addLayer(m)
  })
}

watch(() => props.savedSpots, updateSpotMarkers, { deep: true })
watch(() => props.currentLocation, (loc) => {
  if (map && currentMarker) {
    currentMarker.setLatLng([loc.lat, loc.lon])
  }
}, { deep: true })

onUnmounted(() => {
  if (window.DeviceOrientationEvent) {
    window.removeEventListener('deviceorientation', handleOrientation)
  }
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="relative w-full h-full select-none overflow-hidden">
    <!-- Top Tape Compass -->
    <div class="absolute top-0 left-0 right-0 z-[400] bg-black/85 backdrop-blur-md border-b border-white/10 px-4 pt-2 pb-1.5 text-center text-white">
      <!-- Tape Compass Scale -->
      <div class="relative h-6 overflow-hidden flex items-center justify-center">
        <!-- Center Indicator Pointer -->
        <div class="absolute top-0 w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[6px] border-t-cyan-400 z-10" />

        <!-- Compass Cardinal Points Ruler -->
        <div 
          class="flex items-center gap-7 text-[11px] font-bold tracking-widest text-white/90 transition-transform duration-200"
          :style="{ transform: `translateX(${-heading * 2}px)` }"
        >
          <span>NW</span><span>·</span><span>N</span><span>·</span><span>NE</span><span>·</span>
          <span>E</span><span>·</span><span>SE</span><span>·</span><span>S</span><span>·</span>
          <span>SW</span><span>·</span><span>W</span><span>·</span><span>NW</span><span>·</span><span>N</span>
        </div>
      </div>

      <!-- Heading & Bearing Subtitle -->
      <div class="flex items-center justify-between text-[11px] text-white/70 px-4 mt-0.5">
        <div>
          <span class="text-[9px] text-white/40 block">Direzione</span>
          <span class="font-semibold text-white">{{ heading }}° N</span>
        </div>
        <div class="text-right">
          <span class="text-[9px] text-white/40 block">Angolo di rotta</span>
          <span class="font-semibold text-white">{{ bearing }}° NE</span>
        </div>
      </div>
    </div>

    <!-- Floating Map Search Bar -->
    <div class="absolute top-20 left-3 right-16 sm:right-auto sm:w-96 z-[420]">
      <div class="relative">
        <div class="flex items-center bg-[#07172b]/90 backdrop-blur-xl border border-white/15 rounded-2xl shadow-xl px-3 py-2 text-white">
          <Search class="w-4 h-4 text-cyan-400 mr-2 shrink-0" />
          <input 
            v-model="searchQuery"
            @input="handleSearchInput"
            @focus="showSearchDropdown = searchResults.length > 0"
            type="text" 
            placeholder="Cerca località o tocca la mappa..."
            class="w-full bg-transparent text-xs text-white placeholder-white/45 focus:outline-none"
          />
          <Loader2 v-if="isSearching" class="w-3.5 h-3.5 text-cyan-400 animate-spin ml-2 shrink-0" />
          <button 
            v-else-if="searchQuery" 
            @click="searchQuery = ''; searchResults = []; showSearchDropdown = false"
            class="text-white/50 hover:text-white p-0.5 ml-1"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Search Results Dropdown -->
        <div 
          v-if="showSearchDropdown && searchResults.length" 
          class="absolute top-full left-0 right-0 mt-1.5 bg-[#07172b]/95 backdrop-blur-xl border border-white/15 rounded-2xl shadow-2xl overflow-hidden max-h-56 overflow-y-auto z-[450]"
        >
          <button
            v-for="(r, idx) in searchResults"
            :key="idx"
            @click="handleSelectSearchResult(r)"
            class="w-full flex items-start gap-2.5 px-3.5 py-2.5 hover:bg-white/10 text-left border-b border-white/5 last:border-b-0 transition"
          >
            <MapPin class="w-3.5 h-3.5 text-cyan-400 mt-0.5 shrink-0" />
            <div class="truncate">
              <span class="text-xs font-semibold text-white block">{{ r.name }}</span>
              <span class="text-[10px] text-white/50 block truncate">{{ r.display_name }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Map Leaflet Container -->
    <div ref="mapContainer" class="w-full h-full z-0" />

    <!-- Right Side Floating Controls -->
    <div class="absolute top-20 right-3 z-[400] flex flex-col gap-2.5">
      <!-- Layer Toggle (Satellite vs Street) -->
      <button 
        @click="toggleMapLayer"
        title="Cambia tipo mappa"
        class="w-10 h-10 rounded-xl bg-black/75 backdrop-blur-md border border-white/20 text-white flex items-center justify-center hover:bg-black/90 active:scale-95 transition shadow-lg"
      >
        <Layers class="w-5 h-5 text-cyan-300" />
      </button>

      <!-- Center GPS Location -->
      <button 
        @click="centerOnUser"
        title="Centra la mia posizione"
        class="w-10 h-10 rounded-xl bg-black/75 backdrop-blur-md border border-white/20 text-white flex items-center justify-center hover:bg-black/90 active:scale-95 transition shadow-lg"
      >
        <Navigation class="w-5 h-5 text-cyan-400" />
      </button>
    </div>

    <!-- Bottom Speed Gauge -->
    <div 
      v-if="!inspectedSpot"
      class="absolute bottom-6 left-1/2 -translate-x-1/2 z-[400] bg-black/80 backdrop-blur-md px-4 py-1.5 rounded-full border border-white/15 text-center shadow-lg"
    >
      <span class="text-lg font-bold text-white tracking-wider">--- <span class="text-xs font-normal text-white/60">kn</span></span>
    </div>

    <!-- Floating Spot Action Card (Bottom Sheet on Click/Tap) -->
    <div 
      v-if="inspectedSpot"
      class="absolute bottom-4 left-3 right-3 sm:max-w-md sm:mx-auto z-[450] bg-[#071a33]/95 backdrop-blur-xl border border-cyan-400/30 rounded-2xl p-4 shadow-2xl animate-in slide-in-from-bottom duration-200"
    >
      <div class="flex items-start justify-between gap-2 mb-2">
        <div class="flex items-center gap-2.5 truncate">
          <div class="w-8 h-8 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400 shrink-0">
            <MapPin class="w-4 h-4" />
          </div>
          <div class="truncate">
            <div class="flex items-center gap-2">
              <h4 class="text-sm font-bold text-white truncate">{{ inspectedSpot.name }}</h4>
              <span 
                v-if="inspectedSpot.isMarine"
                class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30 shrink-0"
              >
                Mare/Costa
              </span>
            </div>
            <p class="text-[11px] text-white/60 truncate">{{ inspectedSpot.display_name }}</p>
          </div>
        </div>

        <button 
          @click="closeInspectedSpot" 
          class="text-white/40 hover:text-white p-1 rounded-lg hover:bg-white/10 transition"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Coordinates and Actions -->
      <div class="flex items-center justify-between text-[11px] text-white/50 py-1.5 px-2 bg-black/25 rounded-xl border border-white/5 mb-3">
        <span>Coordinate: {{ inspectedSpot.lat.toFixed(4) }}° N, {{ inspectedSpot.lon.toFixed(4) }}° E</span>
        <span v-if="loadingReverseGeocode" class="text-cyan-400 flex items-center gap-1">
          <Loader2 class="w-3 h-3 animate-spin" /> risoluzione...
        </span>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <!-- Load Forecast Button -->
        <button 
          @click="handleConfirmLoadSpot"
          class="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs shadow-lg active:scale-98 transition"
        >
          <TrendingUp class="w-3.5 h-3.5" />
          Carica Previsioni
        </button>

        <!-- Save Spot Button -->
        <button 
          @click="handleSaveInspectedSpot"
          :disabled="spotSavedSuccess"
          class="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border text-xs font-semibold active:scale-98 transition"
          :class="spotSavedSuccess ? 'bg-emerald-500/20 border-emerald-400/40 text-emerald-300' : 'bg-white/10 hover:bg-white/15 border-white/15 text-white'"
        >
          <Check v-if="spotSavedSuccess" class="w-3.5 h-3.5 text-emerald-400" />
          <Bookmark v-else class="w-3.5 h-3.5 text-amber-300" />
          <span>{{ spotSavedSuccess ? 'Salvato!' : 'Salva nei Preferiti' }}</span>
        </button>
      </div>
    </div>

    <!-- Quick Add Current Location Spot Button '+' -->
    <button 
      v-if="!inspectedSpot"
      @click="emit('addSpot', currentLocation)"
      title="Aggiungi spot corrente"
      class="absolute bottom-5 right-4 z-[400] w-12 h-12 rounded-full bg-cyan-500 hover:bg-cyan-400 active:scale-95 text-white flex items-center justify-center shadow-2xl transition border-2 border-white/30"
    >
      <Plus class="w-6 h-6" />
    </button>
  </div>
</template>
