<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import Header from './components/Header.vue'
import DateCarousel from './components/DateCarousel.vue'
import RadialGauge from './components/RadialGauge.vue'
import ActivityCurveChart from './components/ActivityCurveChart.vue'
import SubNavPills from './components/SubNavPills.vue'
import SubPanels from './components/SubPanels.vue'
import FishingMap from './components/FishingMap.vue'
import BottomNavBar from './components/BottomNavBar.vue'
import SpotSearchModal from './components/SpotSearchModal.vue'
import SavedSpotsModal from './components/SavedSpotsModal.vue'
import ToastNotification from './components/ToastNotification.vue'
import { Loader2, Calendar, Activity } from 'lucide-vue-next'
import { t } from './i18n/index.js'

// Main tabs: 'map', 'forecast', 'spots'
const currentTab = ref('forecast')

// Sub-tabs in mobile forecast: 'activity', 'marine', 'weather', 'sun_moon'
const subTab = ref('activity')

// Sub-tabs for desktop right pane: 'marine', 'weather', 'sun_moon'
const desktopSubTab = ref('marine')

// Active spot (Default coastal spot)
const currentLocation = ref({
  name: 'Porto Antico di Genova',
  lat: 44.407,
  lon: 8.927,
  isMarine: true
})

// Date handling
const todayStr = new Date().toISOString().split('T')[0]
const selectedDate = ref(todayStr)
const summaryDays = ref([])
const forecast = ref(null)
const loading = ref(false)

// Modals
const isSearchOpen = ref(false)
const isFavoritesOpen = ref(false)

// Toast Notifications
const toast = ref({
  visible: false,
  message: '',
  type: 'info'
})

const showToast = (message, type = 'info') => {
  toast.value = {
    visible: true,
    message,
    type
  }
}

// Saved spots in localStorage
const savedSpots = ref([])

const loadSavedSpots = () => {
  try {
    const raw = localStorage.getItem('fishflow_saved_spots')
    if (raw) {
      let parsed = JSON.parse(raw)
      // Transparent migration to clean out obsolete Palermo default
      parsed = parsed.map(s => {
        if (s.name && (s.name.includes('Ottava Circoscrizione') || s.name.toLowerCase().includes('palermo'))) {
          return { id: s.id, name: 'Porto Antico di Genova', lat: 44.407, lon: 8.927, isMarine: true }
        }
        return s
      })
      savedSpots.value = parsed
      localStorage.setItem('fishflow_saved_spots', JSON.stringify(savedSpots.value))
    } else {
      // Default sample spots
      savedSpots.value = [
        { id: '1', name: 'Porto Antico di Genova', lat: 44.407, lon: 8.927, isMarine: true },
        { id: '2', name: 'Porto di Livorno', lat: 43.551, lon: 10.304, isMarine: true },
        { id: '3', name: 'Laguna di Venezia', lat: 45.438, lon: 12.335, isMarine: true }
      ]
      localStorage.setItem('fishflow_saved_spots', JSON.stringify(savedSpots.value))
    }
  } catch (e) {
    savedSpots.value = []
  }
}

const saveSpot = (newSpot) => {
  savedSpots.value.unshift(newSpot)
  localStorage.setItem('fishflow_saved_spots', JSON.stringify(savedSpots.value))
  showToast(t('save_spot') + ': ' + newSpot.name, 'success')
}

const deleteSpot = (id) => {
  savedSpots.value = savedSpots.value.filter(s => s.id !== id)
  localStorage.setItem('fishflow_saved_spots', JSON.stringify(savedSpots.value))
  showToast(t('remove_spot'), 'info')
}

// Fetch 7-day summary for the date carousel
const fetchSummary = async () => {
  try {
    const res = await axios.get('/api/v1/forecast/summary', {
      params: {
        lat: currentLocation.value.lat,
        lon: currentLocation.value.lon,
        days: 7
      }
    })
    summaryDays.value = res.data.days
  } catch (e) {
    console.error('Failed to fetch summary:', e)
  }
}

// Fetch detailed 24h forecast for selected date
const fetchForecast = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/forecast', {
      params: {
        lat: currentLocation.value.lat,
        lon: currentLocation.value.lon,
        date: selectedDate.value
      }
    })
    forecast.value = res.data
  } catch (e) {
    console.error('Failed to fetch forecast:', e)
  } finally {
    loading.value = false
  }
}

const handleSelectDate = (d) => {
  selectedDate.value = d
}

const handleSelectLocation = (loc) => {
  currentLocation.value = loc
  localStorage.setItem('fishflow_current_loc', JSON.stringify(loc))
  fetchSummary()
  fetchForecast()
}

const handleLoadSpotFromMap = (spot) => {
  currentLocation.value = spot
  localStorage.setItem('fishflow_current_loc', JSON.stringify(spot))
  currentTab.value = 'forecast'
  fetchSummary()
  fetchForecast()
  showToast(`${t('spot_set')}: ${spot.name}`, 'info')
}

const applyGpsCoordinates = async (lat, lon) => {
  const formattedLat = parseFloat(lat.toFixed(4))
  const formattedLon = parseFloat(lon.toFixed(4))
  let spotName = `Spot (${formattedLat}, ${formattedLon})`
  let isMarine = true

  try {
    const res = await axios.get('/api/v1/reverse-geocode', {
      params: { lat: formattedLat, lon: formattedLon }
    })
    if (res.data && res.data.name) {
      spotName = res.data.name
      isMarine = res.data.is_marine
    }
  } catch (e) {
    // Fallback to formatted coordinate string
  }

  currentLocation.value = {
    name: spotName,
    lat: formattedLat,
    lon: formattedLon,
    isMarine
  }
  localStorage.setItem('fishflow_current_loc', JSON.stringify(currentLocation.value))

  loading.value = false
  fetchSummary()
  fetchForecast()
  showToast(`${t('gps_detected')}: ${spotName}`, 'success')
}

const fallbackToIpLocation = async (reason = '') => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/location/auto')
    if (res.data && res.data.latitude && res.data.longitude) {
      currentLocation.value = {
        name: res.data.name,
        lat: res.data.latitude,
        lon: res.data.longitude,
        isMarine: res.data.is_marine
      }
      localStorage.setItem('fishflow_current_loc', JSON.stringify(currentLocation.value))
      fetchSummary()
      fetchForecast()
      const msg = reason 
        ? `${t('gps_fallback')}: ${res.data.name}`
        : `${t('ip_detected')}: ${res.data.name}`
      showToast(msg, 'info')
      return
    }
  } catch (e) {
    console.error('Failed to auto-detect location from IP:', e)
  } finally {
    loading.value = false
  }
  showToast(t('gps_fallback'), 'warning')
}

const handleUseGps = () => {
  loading.value = true
  showToast(t('detecting_location'), 'info')

  if (!navigator.geolocation) {
    fallbackToIpLocation('No browser geolocation')
    return
  }

  let hasResponded = false

  // Safety fallback timer: if browser hangs or times out on GPS dialog, immediately fallback to IP
  const timeoutTimer = setTimeout(async () => {
    if (!hasResponded) {
      hasResponded = true
      console.warn('GPS prompt/lookup timed out, falling back to IP Geolocation')
      await fallbackToIpLocation('GPS timeout')
    }
  }, 3500)

  // Use low accuracy first for fast resolution without freezing
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      if (hasResponded) return
      hasResponded = true
      clearTimeout(timeoutTimer)
      await applyGpsCoordinates(pos.coords.latitude, pos.coords.longitude)
    },
    async (err) => {
      if (hasResponded) return
      hasResponded = true
      clearTimeout(timeoutTimer)
      console.warn('GPS error, falling back to IP Geolocation:', err.message)
      await fallbackToIpLocation(err.message)
    },
    { timeout: 3000, enableHighAccuracy: false, maximumAge: 300000 }
  )
}

const currentHeaderTitle = computed(() => {
  if (currentTab.value === 'map') return t('map')
  if (currentTab.value === 'spots') return t('spots')
  if (subTab.value === 'marine') return t('marine')
  if (subTab.value === 'weather') return t('weather')
  if (subTab.value === 'sun_moon') return t('sun_moon')
  return t('activity')
})

const isToday = computed(() => selectedDate.value === todayStr)

watch(() => selectedDate.value, fetchForecast)

onMounted(async () => {
  loadSavedSpots()

  // Check saved active spot
  const savedCurrent = localStorage.getItem('fishflow_current_loc')
  if (savedCurrent) {
    try {
      const parsed = JSON.parse(savedCurrent)
      if (parsed && parsed.lat && parsed.lon) {
        currentLocation.value = parsed
      }
    } catch (e) {}
  } else {
    // Silently auto-detect location from IP on first app visit
    try {
      const res = await axios.get('/api/v1/location/auto')
      if (res.data && res.data.latitude && res.data.longitude) {
        currentLocation.value = {
          name: res.data.name,
          lat: res.data.latitude,
          lon: res.data.longitude,
          isMarine: res.data.is_marine
        }
      }
    } catch (e) {}
  }

  fetchSummary()
  fetchForecast()
})
</script>

<template>
  <!-- Fully Responsive Dynamic Shell: Mobile touch view + Desktop wide dashboard -->
  <div class="h-screen w-full bg-[#030b14] flex flex-col overflow-hidden text-white select-none">
    <div class="w-full max-w-7xl mx-auto flex-1 flex flex-col min-h-0 relative">
      
      <!-- VIEW 1: MAP TAB -->
      <template v-if="currentTab === 'map'">
        <div class="w-full flex-1 flex flex-col min-h-0 overflow-hidden">
          <Header 
            :title="currentHeaderTitle"
            :spot-name="currentLocation.name"
            :current-tab="currentTab"
            :loading="loading"
            @change-tab="(tab) => currentTab = tab"
            @open-search="isSearchOpen = true"
            @use-gps="handleUseGps"
            @open-favorites="isFavoritesOpen = true"
          />
          <div class="flex-1 relative min-h-0">
            <FishingMap 
              :current-location="currentLocation"
              :saved-spots="savedSpots"
              @select-spot="handleSelectLocation"
              @load-spot="handleLoadSpotFromMap"
              @add-spot="saveSpot"
            />
          </div>
        </div>
      </template>

      <!-- VIEW 2: FORECAST TAB -->
      <template v-else-if="currentTab === 'forecast'">
        <!-- Top Header with Desktop Tabs & Mobile Branding -->
        <Header 
          :title="currentHeaderTitle"
          :spot-name="currentLocation.name"
          :current-tab="currentTab"
          :loading="loading"
          @change-tab="(tab) => currentTab = tab"
          @open-search="isSearchOpen = true"
          @use-gps="handleUseGps"
          @open-favorites="isFavoritesOpen = true"
        />

        <!-- Horizontal Date Carousel -->
        <DateCarousel 
          :days="summaryDays"
          :selected-date="selectedDate"
          @select-date="handleSelectDate"
        />

        <!-- Loading State -->
        <div v-if="loading && !forecast" class="flex-1 flex flex-col items-center justify-center">
          <Loader2 class="w-8 h-8 text-sky-400 animate-spin mb-2" />
          <span class="text-xs text-white/60">Caricamento effemeridi e meteo...</span>
        </div>

        <!-- Loaded Forecast View -->
        <template v-else-if="forecast">
          
          <!-- DESKTOP / TABLET DUAL-PANE VIEW (lg and above) -->
          <div class="hidden lg:grid lg:grid-cols-12 gap-4 xl:gap-5 flex-1 min-h-0 p-3 sm:p-4 overflow-hidden">
            <!-- Left Pane: Solunar Fishing Activity Score & 24h Curve -->
            <div class="lg:col-span-5 xl:col-span-4 bg-slate-900/60 backdrop-blur-md rounded-3xl p-3.5 xl:p-4 border border-white/10 shadow-2xl flex flex-col justify-between overflow-y-auto min-h-0">
              <div class="flex items-center justify-between pb-2 border-b border-white/10 shrink-0">
                <div class="flex items-center gap-2">
                  <Activity class="w-4 h-4 text-sky-400" />
                  <span class="text-xs font-bold text-sky-400 tracking-wider uppercase">{{ t('activity') }}</span>
                </div>
                <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-white/5 border border-white/10 text-[11px] font-mono text-sky-300">
                  <Calendar class="w-3.5 h-3.5 text-sky-400" />
                  <span>{{ selectedDate }}</span>
                </div>
              </div>

              <RadialGauge 
                :score="forecast.daily_score"
                :rating="forecast.daily_rating"
              />

              <ActivityCurveChart 
                :hourly-data="forecast.hourly_activity"
                :solunar="forecast.solunar"
                :is-today="isToday"
              />
            </div>

            <!-- Right Pane: Sub-Panels (Maree & Onde, Meteo, Sole e Luna) -->
            <div class="lg:col-span-7 xl:col-span-8 bg-slate-900/60 backdrop-blur-md rounded-3xl p-3.5 xl:p-4 border border-white/10 shadow-2xl flex flex-col min-h-0 overflow-hidden">
              <!-- Sub-Nav Pills for Desktop Right Pane -->
              <SubNavPills 
                :active-tab="desktopSubTab"
                :show-activity="false"
                @change-tab="(tab) => desktopSubTab = tab"
                class="mb-2 shrink-0"
              />
              <!-- Sub-Panel Detailed View -->
              <div class="flex-1 overflow-y-auto min-h-0 pr-1">
                <SubPanels 
                  :sub-tab="desktopSubTab"
                  :forecast="forecast"
                />
              </div>
            </div>
          </div>

          <!-- MOBILE / COMPACT VIEW (< lg) -->
          <div class="lg:hidden w-full max-w-xl mx-auto flex-1 flex flex-col min-h-0 overflow-hidden">
            <!-- Scrollable Content Area -->
            <div class="flex-1 overflow-y-auto min-h-0 px-2 py-1 flex flex-col justify-between">
              <!-- Sub-View: Attività dei pesci -->
              <template v-if="subTab === 'activity'">
                <RadialGauge 
                  :score="forecast.daily_score"
                  :rating="forecast.daily_rating"
                />
                <ActivityCurveChart 
                  :hourly-data="forecast.hourly_activity"
                  :solunar="forecast.solunar"
                  :is-today="isToday"
                  @open-calendar="isSearchOpen = true"
                />
              </template>

              <!-- Other Sub-Views: Maree & Onde, Meteo, Sole e Luna -->
              <template v-else>
                <SubPanels 
                  :sub-tab="subTab"
                  :forecast="forecast"
                />
              </template>
            </div>

            <!-- Mobile Sub-Navigation Pills (Pinned above bottom bar) -->
            <div class="shrink-0 p-2 border-t border-white/5 bg-slate-950/60 backdrop-blur-md">
              <SubNavPills 
                :active-tab="subTab"
                :show-activity="true"
                @change-tab="(tab) => subTab = tab"
              />
            </div>
          </div>
        </template>
      </template>

      <!-- VIEW 3: SPOTS TAB -->
      <template v-else-if="currentTab === 'spots'">
        <Header 
          :title="currentHeaderTitle"
          :spot-name="currentLocation.name"
          :current-tab="currentTab"
          :loading="loading"
          @change-tab="(tab) => currentTab = tab"
          @open-search="isSearchOpen = true"
          @use-gps="handleUseGps"
          @open-favorites="isFavoritesOpen = true"
        />
        <SavedSpotsModal 
          :embedded="true"
          :saved-spots="savedSpots"
          :current-location="currentLocation"
          @select-spot="(s) => { handleSelectLocation(s); currentTab = 'forecast'; }"
          @delete-spot="deleteSpot"
          @save-current-spot="saveSpot"
        />
      </template>

      <!-- Mobile Bottom Navigation Bar (Hidden on md/lg desktop where top nav is present) -->
      <BottomNavBar 
        class="md:hidden"
        :current-tab="currentTab"
        @change-tab="(tab) => currentTab = tab"
      />

      <!-- Spot Search Modal -->
      <SpotSearchModal 
        :is-open="isSearchOpen"
        @close="isSearchOpen = false"
        @select-location="handleSelectLocation"
        @use-gps="handleUseGps"
      />

      <!-- Saved Spots Modal Dialog (when opened via header bell icon) -->
      <SavedSpotsModal 
        v-if="currentTab !== 'spots'"
        :is-open="isFavoritesOpen"
        :embedded="false"
        :saved-spots="savedSpots"
        :current-location="currentLocation"
        @close="isFavoritesOpen = false"
        @select-spot="handleSelectLocation"
        @delete-spot="deleteSpot"
        @save-current-spot="saveSpot"
      />

      <!-- Non-blocking Toast Notification -->
      <ToastNotification
        :visible="toast.visible"
        :message="toast.message"
        :type="toast.type"
        @close="toast.visible = false"
      />
    </div>
  </div>
</template>
