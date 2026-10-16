<template>
  <div v-if="pending" class="swap panel">
    <h3>{{ pending.swap ? '5 — Поменять карту' : '6 — Взять карту сброса' }}</h3>
    <p class="hint">Доступные карты сброса:</p>
    <div class="cards">
      <div v-for="cid in pool" :key="cid" class="card" :class="{ sel: chosen === cid }" @click="choose(cid)">
        <div class="ctitle">{{ title(cid) }}</div>
      </div>
    </div>
    <template v-if="pending.swap && chosen">
      <p class="hint">Какую карту из руки отдать:</p>
      <div class="cards">
        <div v-for="cid in hand" :key="cid" class="card" :class="{ sel: handChosen === cid }" @click="handChosen = cid">
          <div class="ctitle">{{ title(cid) }}</div>
        </div>
      </div>
    </template>
    <div class="btns">
      <button v-if="canTokenSwap" @click="swapToken">Поменять жетон влияния</button>
      <button @click="skip">Пропустить</button>
      <button class="primary" :disabled="!canSubmit" @click="submit">Готово</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SwapPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    actions: { type: Object, default: () => ({}) }
  },
  data() {
    return { chosen: null, handChosen: null }
  },
  computed: {
    pending() {
      const pk = this.state.pending_swap
      return pk && pk.seat === this.mySeat ? pk : null
    },
    pool() {
      return this.pending ? this.pending.pool : []
    },
    hand() {
      return (this.state.players[this.mySeat] || {}).hand || []
    },
    canSubmit() {
      if (!this.pending) return false
      if (this.pending.swap) return !!this.chosen && !!this.handChosen
      return !!this.chosen
    },
    canTokenSwap() {
      return this.pending && this.pending.token_top != null
    }
  },
  watch: {
    pending(nv, ov) {
      if (nv !== ov) { this.chosen = null; this.handChosen = null }
    }
  },
  methods: {
    choose(cid) { this.chosen = cid },
    title(cid) {
      const c = this.state.cards[cid] || {}
      const def = this.actions[c.standard_key]
      return (def && def.title) || String(cid)
    },
    submit() {
      this.$emit('command', { type: 'resolve_swap', seat: this.mySeat, discard_card_id: this.chosen, hand_card_id: this.handChosen })
    },
    skip() {
      this.$emit('command', { type: 'resolve_swap', seat: this.mySeat, discard_card_id: null, hand_card_id: null })
    },
    swapToken() {
      this.$emit('command', { type: 'resolve_swap', seat: this.mySeat, token_swap: true })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.hint { color: #8a6d3b; margin: 0.4rem 0; }
.cards { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.card { min-width: 7rem; border: 1px solid #cfcfcf; border-radius: 0.5rem; padding: 0.5rem; cursor: pointer; background: #fafafa; }
.card.sel { border-color: #2f6fed; background: #eef4ff; }
.ctitle { font-weight: 600; font-size: 0.9rem; }
.btns { display: flex; gap: 0.6rem; margin-top: 0.7rem; }
.btns button { border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; background: #f2f2f2; }
.btns button.primary { background: #2f6fed; color: #fff; }
.btns button.primary:disabled { opacity: 0.5; cursor: default; }
</style>
