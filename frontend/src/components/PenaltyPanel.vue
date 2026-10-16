<template>
  <div v-if="pending" class="backdrop">
    <div class="modal">
      <h3>Штрафное условие</h3>
      <p class="text">В каждом районе города есть хотя бы один шелудивый — все игроки теряют по 1 победному очку.</p>
      <p class="acked">Подтвердили: {{ ackedCount }} / {{ playerCount }}</p>
      <button class="ok" :disabled="acked" @click="ok">{{ acked ? 'Подтверждено' : 'ОК' }}</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PenaltyPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  computed: {
    pending() { return this.state.pending_penalty || null },
    ackedCount() { return this.pending ? (this.pending.acked || []).length : 0 },
    playerCount() { return this.state.player_count || 0 },
    acked() { return this.pending ? (this.pending.acked || []).includes(this.mySeat) : false }
  },
  methods: {
    ok() { this.$emit('command', { type: 'ack_penalty', seat: this.mySeat }) }
  }
}
</script>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45); display: flex; align-items: center; justify-content: center; z-index: 30; }
.modal { background: #fff; border-radius: 0.75rem; padding: 1.5rem; width: 24rem; max-width: 92vw; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25); animation: shake 0.5s ease; }
.text { color: #444; margin: 0.6rem 0; }
.acked { color: #888; font-size: 0.85rem; margin: 0.4rem 0 0.8rem; }
.ok { width: 100%; border: none; border-radius: 0.5rem; padding: 0.6rem; cursor: pointer; background: #2f6fed; color: #fff; font-size: 1rem; }
.ok:disabled { opacity: 0.5; cursor: default; }
</style>
