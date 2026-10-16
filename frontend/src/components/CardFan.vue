<template>
  <div class="fan" :style="fanStyle()">
    <div
      v-for="(cid, i) in cards"
      :key="cid"
      class="card-slot"
      :style="slotStyle(cid, i)"
    >
      <div
        class="card"
        :class="{ dimmed, hovered: hoveredCard === cid, dragging: draggingCard === cid }"
        :style="cardStyle(cid, i)"
        @mouseenter="hoveredCard = cid"
        @mouseleave="hoveredCard = null"
        @pointerdown="onPointerDown(cid, $event)"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp"
        @click="onClick(cid)"
      >
        <img :src="actionCardImage(cid)" class="card-img" :alt="altText(cid)" />
        <div class="card-tooltip">{{ tooltipText(cid) }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { actionCardImage } from '../assets'

export default {
  name: 'CardFan',
  props: {
    cards: { type: Array, required: true },
    state: { type: Object, required: true },
    actions: { type: Object, default: () => ({}) },
    clickable: { type: Boolean, default: true },
    dimmed: { type: Boolean, default: false },
    cardW: { type: Number, default: 92 }
  },
  data() {
    return {
      hoveredCard: null,
      draggingCard: null,
      pressedCard: null,
      wasDragged: false,
      dragStartX: 0,
      dragStartY: 0,
      angleStep: 6.5
    }
  },
  computed: {
    cardH() { return Math.round(this.cardW * 724 / 500) },
    cardStep() { return Math.round(this.cardW * 0.63) }
  },
  methods: {
    actionCardImage,
    fanStyle() {
      return {
        '--fan-w': this.cardW + 'px',
        '--fan-h': this.cardH + 'px',
        '--fan-step': this.cardStep + 'px',
        '--fan-box-h': (this.cardH + 100) + 'px',
        height: 'var(--fan-box-h)'
      }
    },
    slotStyle(cid, i) {
      const n = this.cards.length
      const center = (n - 1) / 2
      const off = i - center
      let z = i + 1
      if (this.draggingCard === cid) z = 1000
      else if (this.hoveredCard === cid) z = 500
      return {
        left: 'calc(50% + (' + off + ') * var(--fan-step) - var(--fan-w) / 2)',
        width: 'var(--fan-w)',
        height: 'var(--fan-h)',
        zIndex: z
      }
    },
    cardStyle(cid, i) {
      const n = this.cards.length
      const center = (n - 1) / 2
      const angle = (i - center) * this.angleStep
      if (this.draggingCard === cid) return { transform: 'rotate(0deg) translateY(-30px)' }
      if (this.hoveredCard === cid) return { transform: 'rotate(' + angle + 'deg) translateY(-16px)' }
      return { transform: 'rotate(' + angle + 'deg)' }
    },
    onPointerDown(cid, e) {
      this.pressedCard = cid
      this.draggingCard = cid
      this.dragStartX = e.clientX
      this.dragStartY = e.clientY
      this.wasDragged = false
    },
    onPointerMove(e) {
      if (this.pressedCard == null) return
      if (Math.abs(e.clientX - this.dragStartX) + Math.abs(e.clientY - this.dragStartY) > 6) {
        this.wasDragged = true
      }
    },
    onPointerUp() {
      this.draggingCard = null
      this.pressedCard = null
    },
    onClick(cid) {
      if (this.wasDragged) { this.wasDragged = false; return }
      if (this.clickable) this.$emit('pick', cid)
    },
    altText(cid) {
      const c = this.state.cards[cid] || {}
      const def = this.actions[c.standard_key]
      return (def && def.title) || String(cid)
    },
    tooltipText(cid) {
      const c = this.state.cards[cid] || {}
      const std = (this.actions[c.standard_key] || {}).title
      const sit = (this.actions[c.situational_key] || {}).title
      return (std || '') + (sit ? '  ·  ' + sit : '')
    }
  }
}
</script>

<style scoped>
.fan { position: relative; }
@media (max-width: 480px) {
  .fan {
    --fan-w: 80px !important;
    --fan-h: 116px !important;
    --fan-step: 50px !important;
    --fan-box-h: 216px !important;
  }
}
.card-slot { position: absolute; bottom: 40px; transform-origin: bottom center; }
.card {
  width: 100%;
  height: 100%;
  position: relative;
  transform-origin: bottom center;
  transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.3, 1), box-shadow 0.22s ease;
  cursor: pointer;
  -webkit-user-select: none;
  user-select: none;
  touch-action: none;
}
.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0.5rem;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
}
.card.hovered .card-img { box-shadow: 0 8px 22px rgba(0, 0, 0, 0.38); }
.card.dragging .card-img { box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5); }
.card.dimmed { opacity: 0.55; }
.card.dimmed .card-img { filter: saturate(0.6); }
.card-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 20, 22, 0.92);
  color: #fff;
  padding: 0.4rem 0.6rem;
  border-radius: 0.4rem;
  font-size: 0.75rem;
  line-height: 1.25;
  white-space: nowrap;
  max-width: 240px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  z-index: 2000;
}
.card:hover .card-tooltip { opacity: 1; }
</style>
