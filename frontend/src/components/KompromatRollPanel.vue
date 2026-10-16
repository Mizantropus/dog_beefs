<template>
  <div v-if="pending" class="kroll panel">
    <h3>{{ isLift ? 'Проверка авторитета' : 'Компромат — бросок кубика' }}</h3>
    <div class="die-wrap">
      <DiceCube :key="face" :face="face" :size="72" />
    </div>
    <p v-if="!isLift" class="hint">
      <img :src="tokenImage" :alt="tokenLabel" class="tok-img" />
      {{ tokenLabel }} <span v-if="isReward" class="badge">наградной</span>
    </p>
    <p v-else class="hint">Выпало: <strong>{{ value }}</strong> · {{ value >= 5 ? 'Успех' : 'Неудача' }}</p>
    <div class="btns">
      <button class="primary" @click="accept">Принять</button>
    </div>
  </div>
</template>

<script>
import { DIE_SYMBOLS, AUTHORITY_TOKEN_VALUES, AUTHORITY_TOKEN_REWARD, authorityTokenLabel } from '../board'
import { authorityTokenImage, dieFaceImage } from '../assets'
import DiceCube from './DiceCube.vue'

export default {
  name: 'KompromatRollPanel',
  components: { DiceCube },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  computed: {
    pending() {
      const pk = this.state.pending_kompromat
      return pk && pk.seat === this.mySeat && !pk.choose ? pk : null
    },
    face() {
      return this.pending ? this.pending.face : 0
    },
    symbol() {
      return DIE_SYMBOLS[this.face] || '?'
    },
    tokenKey() {
      const p = (this.state.players || [])[this.mySeat] || {}
      return (p.authority_line || [])[this.face] || 'dummy'
    },
    tokenLabel() {
      return authorityTokenLabel(this.tokenKey)
    },
    isLift() {
      return this.pending && this.pending.kind === 'lift_kompromat'
    },
    value() {
      return AUTHORITY_TOKEN_VALUES[this.tokenKey] != null ? AUTHORITY_TOKEN_VALUES[this.tokenKey] : 0
    },
    isReward() {
      return !!AUTHORITY_TOKEN_REWARD[this.tokenKey]
    },
    tokenImage() {
      return authorityTokenImage(this.tokenKey, this.mySeat)
    }
  },
  methods: {
    dieFaceImage,
    accept() {
      this.$emit('command', { type: 'resolve_kompromat', seat: this.mySeat, reroll: false })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; text-align: center; }
.die-wrap { margin: 0.5rem 0; }
.die { display: inline-block; font-size: 3.2rem; animation: spin 0.6s ease-out; }
@keyframes spin {
  0% { transform: rotate(0deg) scale(0.4); opacity: 0; }
  60% { transform: rotate(720deg) scale(1.15); opacity: 1; }
  100% { transform: rotate(720deg) scale(1); }
}
.hint { color: #8a6d3b; }
.tok-img { height: 2.4rem; width: auto; vertical-align: middle; }
.die-img { height: 2.6rem; width: auto; vertical-align: middle; }
.badge { display: inline-block; background: #f0b429; color: #fff; border-radius: 0.4rem; padding: 0.1rem 0.4rem; font-size: 0.75rem; margin-left: 0.3rem; }
.btns { display: flex; gap: 0.6rem; justify-content: center; margin-top: 0.6rem; }
.btns button { border: none; border-radius: 0.5rem; padding: 0.55rem 1rem; cursor: pointer; background: #f2f2f2; font-size: 0.95rem; }
.btns button.primary { background: #2f6fed; color: #fff; }
</style>