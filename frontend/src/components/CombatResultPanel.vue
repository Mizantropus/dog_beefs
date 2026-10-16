<template>
  <div v-if="pending && !reactionOpen" class="backdrop">
    <div class="modal">
      <h3>Разыгран жетон</h3>
      <img v-if="tokenImage" :src="tokenImage" :alt="label" class="tok-img" />
      <p class="text">{{ label }}</p>
      <button v-if="isRoller" class="ok" @click="ok">ОК</button>
      <p v-else class="hint">Ожидаем подтверждения атакующего…</p>
    </div>
  </div>
</template>

<script>
import { COMBAT_TOKEN_LABELS } from '../board'
import { combatTokenImage } from '../assets'

export default {
  name: 'CombatResultPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  computed: {
    pending() { return this.state.pending_combat_result || null },
    reactionOpen() { return !!this.state.pending_reaction },
    label() {
      return this.pending ? (COMBAT_TOKEN_LABELS[this.pending.effect] || this.pending.effect) : ''
    },
    tokenImage() {
      return this.pending ? combatTokenImage(this.pending.token, this.pending.roller) : null
    },
    isRoller() { return this.pending ? this.pending.roller === this.mySeat : false }
  },
  methods: {
    ok() { this.$emit('command', { type: 'ack_combat_result', seat: this.mySeat }) }
  }
}
</script>

<style scoped>
.modal { width: 20rem; text-align: center; }
.text { color: #333; font-size: 1.15rem; font-weight: 600; margin: 0.6rem 0 1rem; }
.tok-img { height: 4rem; width: auto; margin: 0.4rem 0; margin-right: 8px; }
.hint { color: #888; margin: 0.6rem 0 0; }
.ok { width: 100%; border: none; border-radius: 0.5rem; padding: 0.6rem; cursor: pointer; background: #2f6fed; color: #fff; font-size: 1rem; }
</style>
