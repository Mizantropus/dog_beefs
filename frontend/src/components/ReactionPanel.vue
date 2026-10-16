<template>
  <div v-if="pending && !amIEligible(state, mySeat)" class="reaction panel waiting">
    <h3>Реакция: {{ triggerLabel }}</h3>
    <p class="hint">Ожидайте ответа других игроков…</p>
  </div>
  <div v-else-if="pending && amIEligible(state, mySeat)" class="reaction panel">
    <h3>Реакция: {{ triggerLabel }}</h3>
    <p class="hint">Можете ответить ситуативной картой или пропустить.</p>
    <div class="actions">
      <div v-for="a in playableActions" :key="a" class="action-row">
        <button class="primary" @click="play(a)">{{ actionLabel(a) }} (карта)</button>
        <button
          v-for="t in kompromatTargets"
          :key="'k' + t"
          @click="play(a, t)"
        >компромат {{ t === mySeat ? 'на себя' : 'на ' + pname(t) }}</button>
      </div>
    </div>
    <div class="btns">
      <button @click="pass">Отмена</button>
    </div>
  </div>
</template>

<script>
import { TRIGGER_LABELS, TRIGGER_ACTIONS, SITUATIONAL_LABELS, cardActionKeys, amIEligible } from '../reactions'

export default {
  name: 'ReactionPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  computed: {
    pending() {
      return this.state.pending_reaction
    },
    triggerLabel() {
      return (this.pending && (TRIGGER_LABELS[this.pending.trigger] || this.pending.trigger)) || ''
    },
    allowedActions() {
      return (this.pending && TRIGGER_ACTIONS[this.pending.trigger]) || []
    },
    playableActions() {
      if (!this.pending) return []
      const p = this.state.players[this.mySeat] || {}
      const hand = p.hand || []
      return this.allowedActions.filter((action) => {
        if (action === 'detonate') {
          const d = this.state.districts[this.pending.to_district] || {}
          const hasBomb = (d.explosives || []).some((e) => e.owner === this.mySeat && e.active)
          if (!hasBomb) return false
        }
        return hand.some((cid) => cardActionKeys((this.state.cards[cid] || {}).situational_key).includes(action))
      })
    },
    hasKompromat() {
      const p = this.state.players[this.mySeat]
      return !!(p && p.kompromat && p.kompromat.length)
    },
    kompromatTargets() {
      const p = this.state.players[this.mySeat] || {}
      return Array.from(new Set(p.kompromat || []))
    }
  },
  methods: {
    pname(seat) {
      const p = (this.state.players || [])[Number(seat)]
      return (p && p.name) || ('Игрок ' + (Number(seat) + 1))
    },
    amIEligible,
    actionLabel(a) {
      return SITUATIONAL_LABELS[a] || a
    },
    matchingCard(action) {
      const p = this.state.players[this.mySeat] || {}
      return (p.hand || []).find((cid) => cardActionKeys((this.state.cards[cid] || {}).situational_key).includes(action))
    },
    play(action, targetSeat) {
      const useKompromat = targetSeat !== undefined
      this.$emit('command', {
        type: 'play_situational',
        seat: this.mySeat,
        action,
        card_id: useKompromat ? null : this.matchingCard(action),
        target_seat: useKompromat ? targetSeat : null
      })
    },
    pass() {
      this.$emit('command', { type: 'pass_reaction', seat: this.mySeat })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.hint { color: #8a6d3b; margin: 0.3rem 0 0.6rem; }
.btns { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.btns button {
  border: none;
  border-radius: 0.5rem;
  padding: 0.55rem 1rem;
  cursor: pointer;
  background: #f2f2f2;
  font-size: 0.95rem;
}
.btns button.primary { background: #d98e04; color: #fff; }
.actions { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.5rem; }
.action-row { display: flex; gap: 0.4rem; }
.action-row button { flex: 1; }
.panel.waiting { background: #f0f0f0; border-color: #ccc; }
</style>