<script setup>
import { ref, watch } from 'vue'
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-vue-next'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'info' // 'info', 'success', 'warning', 'error'
  },
  duration: {
    type: Number,
    default: 4000
  }
})

const emit = defineEmits(['close'])
let timeoutId = null

watch(() => props.visible, (val) => {
  if (timeoutId) clearTimeout(timeoutId)
  if (val && props.duration > 0) {
    timeoutId = setTimeout(() => {
      emit('close')
    }, props.duration)
  }
})
</script>

<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="opacity-0 -translate-y-4 scale-95"
    enter-to-class="opacity-100 translate-y-0 scale-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="opacity-100 translate-y-0 scale-100"
    leave-to-class="opacity-0 -translate-y-4 scale-95"
  >
    <div
      v-if="visible"
      class="fixed top-4 left-4 right-4 sm:left-auto sm:right-4 sm:max-w-md z-[2000] flex items-center justify-between gap-3 p-3.5 rounded-2xl shadow-2xl backdrop-blur-xl border border-white/15 select-none"
      :class="{
        'bg-[#06182c]/95 border-cyan-400/40 text-cyan-200': type === 'info',
        'bg-[#062419]/95 border-emerald-400/40 text-emerald-200': type === 'success',
        'bg-[#281a06]/95 border-amber-400/40 text-amber-200': type === 'warning',
        'bg-[#2a0808]/95 border-red-400/40 text-red-200': type === 'error'
      }"
    >
      <div class="flex items-center gap-2.5 truncate">
        <CheckCircle2 v-if="type === 'success'" class="w-5 h-5 text-emerald-400 shrink-0" />
        <AlertCircle v-else-if="type === 'warning'" class="w-5 h-5 text-amber-400 shrink-0" />
        <AlertCircle v-else-if="type === 'error'" class="w-5 h-5 text-red-400 shrink-0" />
        <Info v-else class="w-5 h-5 text-cyan-400 shrink-0" />

        <span class="text-xs font-medium leading-snug text-white/90">
          {{ message }}
        </span>
      </div>

      <button
        @click="emit('close')"
        class="text-white/40 hover:text-white p-1 rounded-lg hover:bg-white/10 transition shrink-0"
      >
        <X class="w-4 h-4" />
      </button>
    </div>
  </Transition>
</template>

