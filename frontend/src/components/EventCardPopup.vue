<template>
  <div class="card-backdrop" @click.self="$emit('close')">
    <div class="card-modal">
      <h4>Текущее событие</h4>
      <img v-if="def.id != null" :src="eventCardImage(def.id)" class="eimg" :alt="def.title" />
      <div class="etitle">{{ def.title || 'Событие' }}</div>
      <p class="etext">{{ def.text }}</p>
      <button class="ok" @click="$emit('close')">Закрыть</button>
    </div>
  </div>
</template>

<script>
import { eventCardImage } from '../assets'

export default {
  name: 'EventCardPopup',
  props: {
    slug: { type: String, default: '' },
    events: { type: Object, default: () => ({}) }
  },
  computed: {
    def() { return this.events[this.slug] || {} }
  },
  methods: { eventCardImage }
}
</script>

<style scoped>
.card-backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 60; }
.card-modal { background: #fff; border-radius: 0.75rem; padding: 1rem; width: 22rem; max-width: 90vw; text-align: center; box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3); }
.eimg { display: block; width: 160px; margin: 0.5rem auto; border-radius: 0.5rem; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25); }
.etitle { font-weight: 700; font-size: 1.05rem; }
.etext { color: #444; margin: 0.5rem 0; white-space: pre-line; }
.ok { border: none; border-radius: 0.5rem; padding: 0.55rem 1.2rem; cursor: pointer; background: #2f6fed; color: #fff; }
</style>