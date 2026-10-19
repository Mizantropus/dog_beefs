<template>
  <div v-if="pending" class="dbuy panel">
    <h3>Логово — выберите карту из сброса</h3>
    <p class="hint">Вторая карта вернётся наверх колоды сброса.</p>
    <CardFan
      :cards="pending.cards"
      :state="state"
      :actions="actions"
      :clickable="true"
      :card-w="145"
      @pick="pick"
    />
  </div>
</template>

<script>
import CardFan from './CardFan.vue'

export default {
  name: 'DiscardBuyPanel',
  components: { CardFan },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    actions: { type: Object, default: () => ({}) }
  },
  computed: {
    pending() {
      const pdb = this.state.pending_discard_buy
      return pdb && pdb.seat === this.mySeat ? pdb : null
    }
  },
  methods: {
    pick(cid) {
      this.$emit('command', { type: 'pick_discard_buy', seat: this.mySeat, card_id: cid })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff; border: 1px solid #e5e5e5; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; overflow: visible; }
.hint { color: #888; }
</style>