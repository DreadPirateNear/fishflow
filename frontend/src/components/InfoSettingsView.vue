<script setup>
import { Info, ShieldCheck, Server, Compass, ExternalLink } from 'lucide-vue-next'
</script>

<template>
  <div class="flex-1 px-4 py-5 overflow-y-auto select-none space-y-4">
    <!-- App Intro -->
    <div class="bg-white/5 border border-white/10 rounded-2xl p-4 text-center">
      <div class="w-12 h-12 rounded-2xl bg-sky-500/20 border border-sky-400/30 flex items-center justify-center mx-auto mb-2 text-sky-400">
        <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6.5 12c.94-3.46 4.94-6 8.5-6 3.56 0 6.06 2.54 7 6-.94 3.46-3.44 6-7 6s-7.56-2.54-8.5-6Z"/><circle cx="18" cy="10" r="1" fill="currentColor"/></svg>
      </div>
      <h2 class="text-xl font-extrabold text-white">FishFlow</h2>
      <p class="text-xs text-sky-300 font-medium mt-0.5">Motore di Previsione Pesca a Costo Zero</p>
      <p class="text-[11px] text-white/50 mt-2 max-w-sm mx-auto">
        Piattaforma moderna per pescatori sportivi, 100% gratuita, open source e ottimizzata per server Homelab e dispositivi mobile.
      </p>
    </div>

    <!-- Algorithm Explanation -->
    <div class="bg-white/5 border border-white/10 rounded-2xl p-4 space-y-3">
      <div class="flex items-center gap-2 text-white">
        <Compass class="w-5 h-5 text-sky-400" />
        <h3 class="text-sm font-bold">Come Calcoliamo l'Attività</h3>
      </div>
      <p class="text-xs text-white/70 leading-relaxed">
        L'indice orario (0-100) incrocia 4 parametri fisici e biologici determinanti:
      </p>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div class="bg-black/25 p-2.5 rounded-xl border border-white/5">
          <span class="font-bold text-sky-300 block mb-0.5">35% Solunare</span>
          <span class="text-[10px] text-white/60">Picchi Zenit/Nadir (±75m) e Rise/Set con bonus fasi lunari.</span>
        </div>
        <div class="bg-black/25 p-2.5 rounded-xl border border-white/5">
          <span class="font-bold text-emerald-300 block mb-0.5">35% Barometro</span>
          <span class="text-[10px] text-white/60">Derivata $\Delta P$ su 3h: premia cali lenti (-1 a -3 hPa).</span>
        </div>
        <div class="bg-black/25 p-2.5 rounded-xl border border-white/5">
          <span class="font-bold text-amber-300 block mb-0.5">15% Crepuscolo</span>
          <span class="text-[10px] text-white/60">Elevazione solare: boost del 25% tra -6° e +6° (alba e tramonto).</span>
        </div>
        <div class="bg-black/25 p-2.5 rounded-xl border border-white/5">
          <span class="font-bold text-purple-300 block mb-0.5">15% Vento & Nubi</span>
          <span class="text-[10px] text-white/60">Vento ottimale tra 4 e 12 nodi (increspatura specchio).</span>
        </div>
      </div>
    </div>

    <!-- Homelab & Tech Stack -->
    <div class="bg-white/5 border border-white/10 rounded-2xl p-4 space-y-2">
      <div class="flex items-center gap-2 text-white mb-1">
        <Server class="w-5 h-5 text-emerald-400" />
        <h3 class="text-sm font-bold">Architettura Homelab & API</h3>
      </div>
      <ul class="text-xs text-white/70 space-y-1.5 list-disc list-inside">
        <li>Backend FastAPI con motore astronomico offline <strong>PyEphem</strong></li>
        <li>Previsioni orarie e marine via <strong>Open-Meteo</strong> (100% Free)</li>
        <li>Mappa satellitare gratuita ad alta definizione via <strong>Esri World Imagery</strong></li>
        <li>Ricerca toponimi aperta via <strong>OpenStreetMap Nominatim</strong></li>
        <li>Singola porta host containerizzata: <code>8080:80</code> (Proxy interno Nginx)</li>
      </ul>
    </div>
  </div>
</template>
