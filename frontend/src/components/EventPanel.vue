<template>
  <div v-if="event" class="backdrop">
    <div class="modal">
      <h3>Карта события</h3>
      <img v-if="def.id != null" :src="eventCardImage(def.id)" class="eimg" :alt="title" />
      <div class="etitle">{{ title }}</div>
      <p class="etext">{{ text }}</p>
      <p class="acked">Подтвердили: {{ ackedCount }} / {{ playerCount }}</p>
      <button class="ok" :disabled="acked" @click="ok">{{ acked ? 'Подтверждено' : 'ОК' }}</button>
    </div>
  </div>
</template>

<script>
import { eventCardImage } from '../assets'

export default {
  name: 'EventPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    events: { type: Object, default: () => ({}) }
  },
  computed: {
    event() {
      return this.state.pending_event || null
    },
    def() {
      return this.event ? (this.events[this.event.slug] || {}) : {}
    },
    title() {
      return this.def.title || this.def.name || 'Событие'
    },
    text() {
      return this.def.text || this.def.description || ''
    },
    ackedCount() {
      return this.event ? (this.event.acked || []).length : 0
    },
    playerCount() {
      return this.state.player_count || 0
    },
    acked() {
      return this.event ? (this.event.acked || []).includes(this.mySeat) : false
    }
  },
  methods: {
    eventCardImage,
    ok() {
      this.$emit('command', { type: 'ack_event', seat: this.mySeat })
    }
  }
}
</script>

<style scoped>
.modal { width: 24rem; }
.eimg { display: block; width: 170px; margin: 0.6rem auto; border-radius: 0.5rem; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25); }
.etitle { font-weight: 700; font-size: 1.1rem; margin-top: 0.5rem; }
.etext { color: #444; margin: 0.6rem 0; white-space: pre-line; }
.acked { color: #888; font-size: 0.85rem; margin: 0.4rem 0 0.8rem; }
.ok { width: 100%; border: none; border-radius: 0.5rem; padding: 0.6rem; cursor: pointer; background: #2f6fed; color: #fff; font-size: 1rem; }
.ok:disabled { opacity: 0.5; cursor: default; }
</style>