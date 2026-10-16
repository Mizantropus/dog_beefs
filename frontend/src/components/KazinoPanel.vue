<template>
  <div v-if="pending" class="kazino panel">
    <h3>Казино</h3>
    <p class="hint">Банк: {{ pending.pot }}$</p>
    <div class="results">
      <div v-for="s in order" :key="s" class="row" :class="{ cur: s === current }">
        <span>Игрок {{ s + 1 }}<span v-if="s === mySeat"> (вы)</span></span>
        <span>{{ results[s] != null ? results[s] : '—' }}</span>
      </div>
    </div>
    <div v-if="myTurn" class="btns">
      <button :disabled="rolled" @click="roll(false)">Бросить (200$)</button>
      <button :disabled="!rolled || rerolled" @click="roll(true)">Перебросить (100$)</button>
      <button class="primary" @click="finish">Завершить</button>
    </div>
    <p v-else class="hint">Ход игрока {{ current + 1 }}…</p>
  </div>
</template>

<script>
export default {
  name: 'KazinoPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  computed: {
    pending() { return this.state.pending_kazino || null },
    order() { return this.pending ? this.pending.order : [] },
    current() { return this.pending ? this.pending.order[this.pending.idx] : null },
    results() { return this.pending ? this.pending.results : {} },
    rolled() { return this.pending ? this.pending.rolled : false },
    rerolled() { return this.pending ? this.pending.rerolled : false },
    myTurn() { return this.current === this.mySeat }
  },
  methods: {
    roll(reroll) { this.$emit('command', { type: 'kazino', action: reroll ? 'reroll' : 'roll', seat: this.mySeat }) },
    finish() { this.$emit('command', { type: 'kazino', action: 'done', seat: this.mySeat }) }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.hint { color: #8a6d3b; margin: 0.3rem 0; }
.results { display: flex; flex-direction: column; gap: 0.3rem; margin: 0.5rem 0; }
.row { display: flex; justify-content: space-between; padding: 0.3rem 0.5rem; border-radius: 0.4rem; }
.row.cur { background: #eef4ff; font-weight: 600; }
.btns { display: flex; gap: 0.5rem; margin-top: 0.6rem; }
.btns button { border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; background: #f2f2f2; }
.btns button.primary { background: #2f6fed; color: #fff; }
.btns button:disabled { opacity: 0.5; cursor: default; }
</style>
