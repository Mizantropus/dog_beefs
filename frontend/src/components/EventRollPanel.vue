<template>
  <div>
  <div v-if="pending" class="roll panel">
    <h3>{{ title }}</h3>
    <button class="show-event" @click="showCard = true">Показать событие</button>
    <p v-if="isRuletka" class="hint">Целевая масть: <img :src="dieFaceImage(target)" :alt="suitSymbol(target)" class="die-img" /></p>
    <p class="turn">Ходит: {{ pname(current) }}</p>

    <div v-if="!rolled" class="btns">
      <button v-if="current === mySeat" class="primary" @click="roll">Бросить кубик</button>
      <p v-else class="hint">Ожидаем броска…</p>
    </div>
    <div v-else class="result">
      <p class="die-line">
        Выпало:
        <DiceCube :key="current + ':' + currentFace + ':' + (pending.rolls || 0)" :face="currentFace" :size="56" />
        <template v-if="!isRuletka">
          <img :src="tokenImage" :alt="tokenLabel" :title="tokenLabel" class="tok-img" />
          <strong class="val">{{ result }}</strong>
          <span v-if="resultReward" class="badge">наградной</span>
        </template>
      </p>
      <button v-if="current === mySeat" class="primary" @click="ok">ОК</button>
      <p v-else class="hint">Ожидаем…</p>
    </div>

    <p class="results">{{ resultsSummary }}</p>
  </div>
  <EventCardPopup v-if="pending && showCard" :slug="slug" :events="events" @close="showCard = false" />
</div>
</template>

<script>
import { DIE_SYMBOLS, AUTHORITY_TOKEN_VALUES, authorityTokenLabel } from '../board'
import { dieFaceImage, authorityTokenImage } from '../assets'
import DiceCube from './DiceCube.vue'
import EventCardPopup from './EventCardPopup.vue'

export default {
  name: 'EventRollPanel',
  components: { DiceCube, EventCardPopup },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    events: { type: Object, default: () => ({}) }
  },
  data() {
    return { DIE_SYMBOLS, showCard: false }
  },
  computed: {
    pending() { return this.state.pending_event_roll || null },
    slug() { return this.pending ? this.pending.slug : '' },
    def() { return this.pending ? (this.events[this.pending.slug] || {}) : {} },
    title() { return this.def.title || 'Событие' },
    isRuletka() { return this.slug === 'russkaya_ruletka' },
    target() { return this.pending ? this.pending.target : null },
    current() { return this.pending ? this.pending.order[this.pending.idx] : null },
    rolled() { return this.pending ? this.pending.rolled : false },
    result() {
      if (!this.pending || this.current == null) return null
      return this.pending.results[this.current]
    },
    currentFace() {
      if (this.current == null) return 0
      const faces = (this.pending && this.pending.faces) || {}
      return faces[this.current] != null ? faces[this.current] : 0
    },
    tokenKey() {
      const p = (this.state.players || [])[this.current] || {}
      return (p.authority_line || [])[this.currentFace] || 'dummy'
    },
    tokenImage() {
      return authorityTokenImage(this.tokenKey, this.current)
    },
    tokenLabel() {
      return authorityTokenLabel(this.tokenKey)
    },
    resultLabel() {
      if (this.result == null) return ''
      return this.isRuletka ? this.suitSymbol(this.result) : String(this.result)
    },
    resultReward() {
      if (!this.pending || this.current == null) return false
      return !!((this.pending.rewards || {})[this.current])
    },
    resultsSummary() {
      if (!this.pending) return ''
      const parts = []
      for (const seat of this.pending.order) {
        const v = this.pending.results[seat]
        if (v == null) continue
        const label = this.isRuletka ? this.suitSymbol(v) : String(v)
        parts.push(this.pname(seat) + ': ' + label)
      }
      return parts.length ? 'Броски: ' + parts.join(' · ') : ''
    }
  },
  methods: {
    dieFaceImage,
    pname(seat) {
      const p = (this.state.players || [])[Number(seat)]
      return (p && p.name) || ('Игрок ' + (Number(seat) + 1))
    },
    suitSymbol(face) { return DIE_SYMBOLS[face] || '?' },
    roll() { this.$emit('command', { type: 'event_roll', seat: this.mySeat, action: 'roll' }) },
    ok() { this.$emit('command', { type: 'event_roll', seat: this.mySeat, action: 'ok' }) }
  }
}
</script>

<style scoped>
.panel { background: #eef6ff; border: 1px solid #9bc4ff; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.hint { color: #888; margin: 0.3rem 0; }
.turn { color: #2f6fed; font-weight: 600; margin: 0.3rem 0; }
.btns { display: flex; gap: 0.5rem; }
.btns button { border: none; border-radius: 0.5rem; padding: 0.55rem 1rem; cursor: pointer; background: #f2f2f2; }
.btns button.primary { background: #2f6fed; color: #fff; }
.result { margin-top: 0.5rem; }
.result .primary { border: none; border-radius: 0.5rem; padding: 0.55rem 1.2rem; cursor: pointer; background: #2f6fed; color: #fff; }
.die { display: inline-block; font-size: 1.9rem; font-weight: 700; animation: spin 0.5s ease-out; }
.die-img { height: 2.6rem; width: auto; vertical-align: middle; animation: spin 0.5s ease-out; }
.tok-img { height: 2.4rem; width: auto; vertical-align: middle; margin-right: 8px;}
.val { font-size: 1.15rem; font-weight: 700; margin-left: 0.3rem; }
@keyframes spin { 0% { transform: rotate(0deg) scale(0.4); opacity: 0; } 60% { transform: rotate(720deg) scale(1.15); opacity: 1; } 100% { transform: rotate(720deg) scale(1); } }
.die-line { margin: 0.4rem 0; }
.results { color: #666; font-size: 0.85rem; margin-top: 0.5rem; }
.badge { display: inline-block; background: #f0b429; color: #fff; border-radius: 0.4rem; padding: 0.1rem 0.4rem; font-size: 0.75rem; margin-left: 0.3rem; }
.show-event { border: 1px solid #9bc4ff; background: #fff; color: #2f6fed; border-radius: 0.5rem; padding: 0.25rem 0.6rem; cursor: pointer; font-size: 0.85rem; margin-left: 0.5rem; }
</style>
