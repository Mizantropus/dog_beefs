<template>
  <div v-if="pending" class="tswap panel">
    <h3>5 — Обмен жетона влияния</h3>
    <p>Доступные жетоны:</p>
    <div class="drawn">
      <img v-for="(t, i) in drawn" :key="i" :src="tokenImage(t)" :alt="label(t)" :title="label(t)" class="tok-img" />
    </div>
    <div class="form">
      <select v-model="line">
        <option value="authority">Линия авторитета</option>
        <option value="combat">Линия боя</option>
      </select>
      <select v-model="slot">
        <option v-for="i in 6" :key="i" :value="i - 1">Слот {{ i }}</option>
      </select>
      <select v-if="drawn.length > 1" v-model="chosenIndex">
        <option v-for="(t, i) in drawn" :key="i" :value="i">{{ label(t) }}</option>
      </select>
      <button class="primary" @click="submit">Обменять</button>
    </div>
  </div>
</template>

<script>
import { COMBAT_TOKEN_LABELS, AUTHORITY_TOKEN_VALUES, authorityTokenLabel } from '../board'
import { combatTokenImage, authorityTokenImage } from '../assets'

export default {
  name: 'TokenSwapPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  data() {
    return { line: 'authority', slot: 0, chosenIndex: 0 }
  },
  computed: {
    pending() {
      const pts = this.state.pending_token_swap
      return pts && pts.seat === this.mySeat ? pts : null
    },
    drawn() { return this.pending ? this.pending.drawn : [] },
    drawnLabels() { return this.drawn.map((t) => this.label(t)) }
  },
  methods: {
    label(t) {
      if (AUTHORITY_TOKEN_VALUES[t] != null) return authorityTokenLabel(t)
      return COMBAT_TOKEN_LABELS[t] || t
    },
    tokenImage(t) {
      if (AUTHORITY_TOKEN_VALUES[t] != null) return authorityTokenImage(t, this.mySeat)
      return combatTokenImage(t, this.mySeat)
    },
    submit() {
      this.$emit('command', { type: 'resolve_token_swap', seat: this.mySeat, line: this.line, slot: this.slot, chosen_index: this.chosenIndex })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.drawn { display: flex; gap: 0.5rem; margin: 0.4rem 0; }
.tok-img { height: 2.4rem; width: auto; margin-right: 8px; }
.form { display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; margin-top: 0.5rem; }
.form select { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
button.primary { background: #2f6fed; color: #fff; border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; }
</style>
