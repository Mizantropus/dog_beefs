<template>
  <div v-if="pending" class="influence panel">
    <h3>Жетон влияния</h3>
    <p>Вы получили жетон <img :src="tokenImage(pending.token)" :alt="tokenLabel" class="tok-img" /> <strong>{{ tokenLabel }}</strong>. Куда положить?</p>
    <div class="slots">
      <button v-for="(t, i) in line" :key="i" class="slot" @click="choose(i)">
        <span class="idx">Слот {{ i + 1 }}</span>
        <img :src="tokenImage(t)" :alt="tokenLabelOf(t)" :title="tokenLabelOf(t)" class="tok-img" />
      </button>
    </div>
    <button class="po" @click="choose(null)">Сразу в победное очко</button>
  </div>
</template>

<script>
import { COMBAT_TOKEN_LABELS, AUTHORITY_TOKEN_LABELS, authorityTokenLabel } from '../board'
import { combatTokenImage, authorityTokenImage } from '../assets'

export default {
  name: 'InfluencePanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  computed: {
    pending() {
      return (this.state.pending_influence || []).find((e) => e.seat === this.mySeat) || null
    },
    isCombat() {
      return this.pending ? this.pending.token in COMBAT_TOKEN_LABELS : false
    },
    line() {
      if (!this.pending) return []
      const p = this.state.players[this.mySeat] || {}
      return this.isCombat ? p.combat_line || [] : p.authority_line || []
    },
    tokenLabel() {
      return this.pending ? this.tokenLabelOf(this.pending.token) : ''
    }
  },
  methods: {
    tokenLabelOf(tok) {
      if (tok in COMBAT_TOKEN_LABELS) return COMBAT_TOKEN_LABELS[tok]
      return authorityTokenLabel(tok)
    },
    tokenImage(tok) {
      if (tok in COMBAT_TOKEN_LABELS) return combatTokenImage(tok, this.mySeat)
      return authorityTokenImage(tok, this.mySeat)
    },
    choose(slot) {
      this.$emit('command', { type: 'choose_influence', seat: this.mySeat, swap_slot: slot })
    }
  }
}
</script>

<style scoped>
.panel { background: #eef6ff; border: 1px solid #9bc4ff; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.slots { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.6rem 0; }
.slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid #cfcfcf;
  border-radius: 0.5rem;
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  background: #fafafa;
  font-size: 0.8rem;
}
.slot:hover { border-color: #2f6fed; }
.idx { color: #888; }
.tok-img { height: 2.2rem; width: auto; margin-right: 8px;}
.po {
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 0.9rem;
  cursor: pointer;
  background: #2f6fed;
  color: #fff;
  font-size: 0.9rem;
}
</style>