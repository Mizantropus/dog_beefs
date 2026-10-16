<template>
  <div v-if="pending" class="peek panel">
    <h3>Радиостанция: верхние события</h3>
    <div class="cards">
      <div v-for="(slug, i) in pending.cards" :key="i" class="card">
        <img v-if="eventId(slug) != null" :src="eventCardImage(eventId(slug))" class="card-img" :alt="title(slug)" :title="title(slug)" />
        <strong>Событие {{ i + 1 }}</strong>
      </div>
    </div>
    <div class="btns">
      <button v-for="(slug, i) in pending.cards" :key="'d' + i" @click="discard(i)">
        Сбросить (300$): {{ title(slug) }}
      </button>
      <button class="primary" @click="keep">Вернуть обе</button>
    </div>
  </div>
</template>

<script>
import { eventCardImage } from '../assets'

export default {
  name: 'PeekPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    events: { type: Object, default: () => ({}) }
  },
  computed: {
    pending() {
      return this.state.pending_peek && this.state.pending_peek.seat === this.mySeat
        ? this.state.pending_peek : null
    }
  },
  methods: {
    eventCardImage,
    eventId(slug) {
      return (this.events[slug] && this.events[slug].id) || null
    },
    title(slug) {
      return (this.events[slug] && this.events[slug].title) || slug
    },
    discard(i) {
      this.$emit('command', { type: 'resolve_peek', seat: this.mySeat, discard_index: i })
    },
    keep() {
      this.$emit('command', { type: 'resolve_peek', seat: this.mySeat, discard_index: null })
    }
  }
}
</script>

<style scoped>
.panel { background: #eef6ff; border: 1px solid #9bc4ff; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.cards { display: flex; gap: 0.6rem; margin: 0.5rem 0; }
.card { flex: 1; border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.6rem; background: #fafafa; display: flex; flex-direction: column; align-items: center; gap: 0.4rem; }
.card-img { width: 90px; border-radius: 0.4rem; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2); }
.btns { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.btns button { border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; background: #f2f2f2; font-size: 0.9rem; }
.btns button.primary { background: #2f6fed; color: #fff; }
</style>