import { ref, computed } from 'vue'

const savedLang = (() => {
  try {
    return localStorage.getItem('fishflow_lang') || 'it'
  } catch (e) {
    return 'it'
  }
})()

export const currentLang = ref(savedLang)

export const setLanguage = (lang) => {
  currentLang.value = lang
  try {
    localStorage.setItem('fishflow_lang', lang)
  } catch (e) {}
}

export const toggleLanguage = () => {
  setLanguage(currentLang.value === 'it' ? 'en' : 'it')
}

export const translations = {
  it: {
    // Navigation & Tabs
    map: 'Mappa',
    forecast: 'Previsioni',
    spots: 'I tuoi spot',
    me: 'Info & App',
    activity: 'Attività dei pesci',
    marine: 'Maree & Onde',
    weather: 'Meteo',
    sun_moon: 'Sole e Luna',

    // Ratings
    rating_excellent: 'Eccellente',
    rating_good: 'Buona',
    rating_average: 'Media',
    rating_low: 'Bassa',
    rating_very_low: 'Molto bassa',

    // Solunar & Activity
    solunar_day_rating: 'Valutazione Solunare',
    major_times: 'Attività Maggiore',
    minor_times: 'Attività Minore',
    moon_zenith: 'Zenit Lunare',
    moon_nadir: 'Nadir Lunare',
    moon_rise: 'Levata Luna',
    moon_set: 'Calo Luna',
    hourly_activity_curve: 'Andamento 24h Attività',
    realtime_score: 'Indice in tempo reale',

    // Marine tab
    marine_conditions: 'Condizioni del mare attuali',
    sea_temperature: 'Temperatura mare',
    currents: 'Correnti',
    live_tide: 'Marea in tempo reale',
    current_tide: 'Alta marea attuale',
    rising: 'Crescente',
    falling: 'Calante',
    next_high_tide: 'Prossima alta marea',
    next_low_tide: 'Prossima bassa marea',
    low_tide: 'Bassa marea',
    high_tide: 'Alta marea',
    wave_conditions: 'Moto ondoso',
    wave_height: 'Altezza onde',
    wave_period: 'Periodo',
    wave_direction: 'Direzione',
    inland_water: 'Spot in Acque Interne',
    inland_water_desc: 'Questo spot si trova in un bacino o canale interno privo di dati idrografici marini.',

    // Weather tab
    current_conditions: 'Condizioni attuali',
    precipitation: 'Precipitazioni',
    rain_probability: 'Probabilità pioggia',
    pressure: 'Pressione',
    humidity: 'Umidità',
    uv_index: 'Indice UV',
    uv_low: 'Basso',
    uv_moderate: 'Moderato',
    uv_very_high: 'Molto alto',
    temperature: 'Temperatura',
    wind: 'Vento',
    current_wind: 'Vento attuale',
    wind_direction: 'La direzione',
    wind_speed: 'Velocità',
    wind_gusts: 'Raffiche di vento',
    light_breeze: 'Brezza leggera',
    gentle_breeze: 'Brezza tesa',
    strong_breeze: 'Vento forte',
    storm: 'Burrasca',
    rain_radar_preview: 'Radar della pioggia',

    // Sun & Moon
    moon: 'Luna',
    sun: 'Sole',
    distance: 'Distanza',
    illumination: 'Illuminazione',
    moon_age: "L'età",
    days: 'giorni',
    moon_rise_time: 'Sorgere della luna',
    moon_set_time: 'Luna calante',
    day_duration: 'Giorno',
    night_duration: 'Notte',
    sunrise: 'La levata del sole',
    sunset: 'Il tramonto',
    solar_noon: 'Mezzogiorno',
    dawn: 'Alba',
    dusk: 'Crepuscolo',
    midnight: 'Mezzanotte',

    // General & actions
    use_gps: 'Usa posizione',
    detecting_location: 'Rilevamento posizione in corso...',
    search_spot: 'Cerca uno spot o una città...',
    load_spot: 'Carica Spot',
    spot_set: 'Spot impostato',
    gps_detected: 'Posizione rilevata da GPS',
    ip_detected: 'Posizione rilevata da rete IP',
    gps_fallback: 'GPS non disponibile: rilevata posizione approssimativa da IP',
    favorites: 'Preferiti',
    save_spot: 'Salva nei preferiti',
    remove_spot: 'Rimuovi dai preferiti'
  },
  en: {
    // Navigation & Tabs
    map: 'Map',
    forecast: 'Forecast',
    spots: 'Your Spots',
    me: 'Info & App',
    activity: 'Fish Activity',
    marine: 'Tides & Waves',
    weather: 'Weather',
    sun_moon: 'Sun & Moon',

    // Ratings
    rating_excellent: 'Excellent',
    rating_good: 'Good',
    rating_average: 'Moderate',
    rating_low: 'Low',
    rating_very_low: 'Very low',

    // Solunar & Activity
    solunar_day_rating: 'Solunar Evaluation',
    major_times: 'Major Activity',
    minor_times: 'Minor Activity',
    moon_zenith: 'Moon Zenith',
    moon_nadir: 'Moon Nadir',
    moon_rise: 'Moonrise',
    moon_set: 'Moonset',
    hourly_activity_curve: '24h Activity Trend',
    realtime_score: 'Realtime Score',

    // Marine tab
    marine_conditions: 'Current sea conditions',
    sea_temperature: 'Sea temperature',
    currents: 'Currents',
    live_tide: 'Live Tide',
    current_tide: 'Current tide level',
    rising: 'Rising',
    falling: 'Falling',
    next_high_tide: 'Next high tide in',
    next_low_tide: 'Next low tide in',
    low_tide: 'Low tide',
    high_tide: 'High tide',
    wave_conditions: 'Waves & Swell',
    wave_height: 'Wave height',
    wave_period: 'Period',
    wave_direction: 'Direction',
    inland_water: 'Inland Water Spot',
    inland_water_desc: 'This spot is in an inland lake, river, or channel without marine hydrographic sensors.',

    // Weather tab
    current_conditions: 'Current conditions',
    precipitation: 'Precipitation',
    rain_probability: 'Rain probability',
    pressure: 'Pressure',
    humidity: 'Humidity',
    uv_index: 'UV Index',
    uv_low: 'Low',
    uv_moderate: 'Moderate',
    uv_very_high: 'Very high',
    temperature: 'Temperature',
    wind: 'Wind',
    current_wind: 'Current wind',
    wind_direction: 'Direction',
    wind_speed: 'Speed',
    wind_gusts: 'Wind gusts',
    light_breeze: 'Light breeze',
    gentle_breeze: 'Moderate breeze',
    strong_breeze: 'Strong wind',
    storm: 'Gale / Storm',
    rain_radar_preview: 'Rain Radar',

    // Sun & Moon
    moon: 'Moon',
    sun: 'Sun',
    distance: 'Distance',
    illumination: 'Illumination',
    moon_age: 'Age',
    days: 'days',
    moon_rise_time: 'Moonrise',
    moon_set_time: 'Moonset',
    day_duration: 'Day',
    night_duration: 'Night',
    sunrise: 'Sunrise',
    sunset: 'Sunset',
    solar_noon: 'Solar Noon',
    dawn: 'Dawn',
    dusk: 'Dusk',
    midnight: 'Midnight',

    // General & actions
    use_gps: 'Use location',
    detecting_location: 'Detecting location...',
    search_spot: 'Search a spot or city...',
    load_spot: 'Load Spot',
    spot_set: 'Spot updated',
    gps_detected: 'Location detected via GPS',
    ip_detected: 'Location detected via IP network',
    gps_fallback: 'GPS unavailable: approximate location detected via IP',
    favorites: 'Favorites',
    save_spot: 'Save to favorites',
    remove_spot: 'Remove from favorites'
  }
}

export const t = (key) => {
  const dict = translations[currentLang.value] || translations.it
  return dict[key] || key
}

