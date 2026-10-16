<template>
  <div class="pboard" :class="{ nohead: !collapsible }">
    <button v-if="collapsible" type="button" class="phead" :class="{ open: !collapsed }" @click="collapsed = !collapsed">
      <span class="arrow" :class="{ open: !collapsed }">▸</span>
      <span class="phead-title">{{ title }}</span>
    </button>
    <transition name="collapse">
      <div v-if="showPad" class="pad" :style="{ backgroundImage: 'url(' + padImage() + ')' }">
      <!-- ПО -->
      <div class="row" :style="rowStyle('po')">
        <span v-for="i in 6" :key="'po' + i" class="po-slot">
          <img v-if="i <= p.victory_points" :src="tokenBackImage(poBack, mySeat)" class="po-back" :alt="'ПО ' + i" />
        </span>
      </div>
      <!-- Авторитет -->
      <div class="row" :style="rowStyle('authority')">
        <span v-for="(tok, i) in authorityOrdered" :key="'a' + i" class="token-wrap">
          <img :src="authorityTokenImage(tok, mySeat)" class="token" :alt="tok" />
          <span class="token-tooltip">{{ authorityLabel(tok) }}</span>
        </span>
      </div>
      <!-- Бой -->
      <div class="row" :style="rowStyle('combat')">
        <span v-for="(tok, i) in combatOrdered" :key="'c' + i" class="token-wrap">
          <img :src="combatTokenImage(tok, mySeat)" class="token" :alt="tok" />
          <span class="token-tooltip">{{ combatLabel(tok) }}</span>
        </span>
      </div>
    </div>
    </transition>
  </div>
</template>

<script>
import { COMBAT_TOKEN_LABELS, authorityTokenLabel } from '../board'
import { padImage, authorityTokenImage, combatTokenImage, tokenBackImage } from '../assets'

// Порядок граней на планшете (слева направо): кость, носик, ошейник, конура, мячик, миска
// -> индексы в бэкенде: кость=0, носик=1, ошейник=5, конура=3, мячик=4, миска=2
const FACE_ORDER = [0, 1, 5, 3, 4, 2]

export default {
  name: 'PlayerBoard',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    title: { type: String, default: 'Ваш планшет' },
    collapsible: { type: Boolean, default: true }
  },
  data() {
    return {
      collapsed: false,
      FACE_ORDER,
      padLayout: {
        x: 27.2,      // % от левого края (общий для всех строк)
        width: 63.5, // % ширина строки (общая)
        rowH: 15,  // % высота строки (общая)
        poBack: 'authority', // тип оборота для ПО ('authority' | 'combat')
        y: {       // % от верхнего края (по строкам)
          po: 13.5,
          authority: 37,
          combat: 61.3
        }
      }
    }
  },
  computed: {
    showPad() { return !this.collapsible || !this.collapsed },
    p() { return this.state.players[this.mySeat] || {} },
    authorityOrdered() {
      const line = this.p.authority_line || []
      return this.FACE_ORDER.map((i) => line[i] || '')
    },
    combatOrdered() {
      const line = this.p.combat_line || []
      return this.FACE_ORDER.map((i) => line[i] || '')
    }
  },
  methods: {
    padImage,
    authorityTokenImage,
    combatTokenImage,
    tokenBackImage,
    rowStyle(name) {
      return {
        left: this.padLayout.x + '%',
        width: this.padLayout.width + '%',
        top: this.padLayout.y[name] + '%',
        height: this.padLayout.rowH + '%'
      }
    },
    authorityLabel(tok) { return authorityTokenLabel(tok) },
    combatLabel(tok) { return COMBAT_TOKEN_LABELS[tok] || tok }
  }
}
</script>

<style scoped>
.pboard { margin-top: 1rem; }
.phead {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  border: 1px solid #e5e5e5;
  background: #f7f8fa;
  border-radius: 0.6rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  text-align: left;
  margin: 0;
  transition: border-radius 0.25s ease;
}
.phead.open { border-radius: 0.6rem 0.6rem 0 0; }
.phead:hover { background: #eef1f5; }
.arrow { display: inline-block; transition: transform 0.2s ease; color: #666; }
.arrow.open { transform: rotate(90deg); }
.pad {
  position: relative;
  aspect-ratio: 1800 / 919;
  background-size: 100% 100%;
  background-repeat: no-repeat;
  border-radius: 0 0 0.9rem 0.9rem;
  box-shadow: var(--shadow-md);
  overflow: hidden;
}
.pboard.nohead { margin-top: 0; }
.pboard.nohead .pad { border-radius: 0.9rem; }
.collapse-enter-active, .collapse-leave-active {
  transition: max-height 0.35s ease, opacity 0.3s ease;
  overflow: hidden;
}
.collapse-enter, .collapse-leave-to {
  max-height: 0;
  opacity: 0;
}
.collapse-enter-to, .collapse-leave {
  max-height: 1000px;
  opacity: 1;
}
.row {
  position: absolute;
  display: flex;
  justify-content: space-between;
  flex-wrap: nowrap;
  align-items: center;
}
.token-wrap { position: relative; height: 100%; max-width: 15%; display: inline-flex; align-items: center; justify-content: center; }
.token {
  height: 100%;
  width: auto;
  max-width: 100%;
  object-fit: contain;
  pointer-events: none;
}
.token-tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 20, 22, 0.92);
  color: #fff;
  padding: 0.3rem 0.5rem;
  border-radius: 0.4rem;
  font-size: 0.7rem;
  line-height: 1.2;
  white-space: nowrap;
  max-width: 220px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  z-index: 50;
}
.token-wrap:hover .token-tooltip { opacity: 1; }
.po-slot { height: 100%; aspect-ratio: 1; }
.po-back { width: 100%; height: 100%; object-fit: contain; pointer-events: none; animation: pop 0.28s cubic-bezier(0.2, 0.8, 0.3, 1); }
</style>
