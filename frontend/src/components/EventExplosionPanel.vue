<template>
  <div v-if="pending" class="exp panel">
    <h3>Взрыв! Проверка авторитета</h3>
    <p class="hint">Район {{ districtName }} · Пёс игрока {{ current + 1 }} ({{ idx + 1 }} / {{ queue.length }})</p>
    <div v-if="value != null" class="die-wrap">
      <DiceCube :key="idx + ':' + face" :face="face" :size="56" />
      <img :src="tokenImage" :alt="tokenLabel" :title="tokenLabel" class="tok-img" />
      <strong class="val">{{ value }}</strong>
    </div>
    <p v-if="value != null" class="result">{{ value <= 3 ? 'Пёс погибает' : 'Пёс выживает' }}</p>
    <div class="btns">
      <button v-if="value == null" class="primary" :disabled="!myTurn" @click="roll">Бросить кубик</button>
      <button v-else class="primary" :disabled="!myTurn || reactionOpen" @click="ok">ОК</button>
    </div>
    <p v-if="!myTurn" class="hint">Ход игрока {{ current + 1 }}…</p>
  </div>
</template>

<script>
import { authorityTokenLabel } from '../board'
import { authorityTokenImage } from '../assets'
import DiceCube from './DiceCube.vue'

export default {
  name: 'EventExplosionPanel',
  components: { DiceCube },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  computed: {
    pending() { return this.state.pending_event_explosion || null },
    queue() { return this.pending ? this.pending.queue : [] },
    idx() { return this.pending ? this.pending.idx : 0 },
    value() { return this.pending ? this.pending.value : null },
    face() { return this.pending && this.pending.face != null ? this.pending.face : 0 },
    current() { return this.pending ? this.pending.queue[this.pending.idx] : null },
    myTurn() { return this.current === this.mySeat },
    reactionOpen() { return !!this.state.pending_reaction },
    districtId() { return this.pending ? this.pending.district_id : null },
    districtName() {
      const id = this.districtId
      if (id == null) return ''
      const nm = (this.districts[id] && this.districts[id].name) || ''
      return nm ? (id + ' · ' + nm) : ('Район ' + id)
    },
    tokenKey() {
      const p = (this.state.players || [])[this.current] || {}
      return (p.authority_line || [])[this.face] || 'dummy'
    },
    tokenImage() {
      return authorityTokenImage(this.tokenKey, this.current)
    },
    tokenLabel() {
      return authorityTokenLabel(this.tokenKey)
    }
  },
  methods: {
    roll() { this.$emit('command', { type: 'event_explosion', action: 'roll', seat: this.mySeat }) },
    ok() { this.$emit('command', { type: 'event_explosion', action: 'ok', seat: this.mySeat }) }
  }
}
</script>

<style scoped>
.panel { background: #fdeeee; border: 1px solid #e0a0a0; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; text-align: center; animation: shake 0.5s ease; }
.hint { color: #8a4040; margin: 0.3rem 0; }
.die-wrap { margin: 0.5rem 0; display: flex; align-items: center; justify-content: center; gap: 0.4rem; }
.result { color: #b03030; font-weight: 600; margin: 0.3rem 0 0; }
.tok-img { height: 2.4rem; width: auto; vertical-align: middle; }
.val { font-size: 1.2rem; font-weight: 700; }
.btns { display: flex; gap: 0.5rem; justify-content: center; margin-top: 0.6rem; }
.btns button { border: none; border-radius: 0.5rem; padding: 0.5rem 1rem; cursor: pointer; background: #f2f2f2; }
.btns button.primary { background: #2f6fed; color: #fff; }
.btns button:disabled { opacity: 0.5; cursor: default; }
</style>
