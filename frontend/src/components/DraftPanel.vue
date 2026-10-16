<template>
  <div class="draft panel">
    <h3>Драфт карт — сделка {{ state.draft.deal }} из 2</h3>
    <p v-if="picked" class="hint">Вы уже выбрали карту. Ждём остальных…</p>

    <template v-else>
      <CardFan
        :cards="draftHand"
        :state="state"
        :actions="actions"
        :clickable="!picked"
        :card-w="145"
        @pick="pick"
      />
    </template>

    <div v-if="myHand.length" class="mine">
      <h4>Ваши карты ({{ myHand.length }})</h4>
      <CardFan
        :cards="myHand"
        :state="state"
        :actions="actions"
        :clickable="false"
        :card-w="145"
      />
    </div>
  </div>
</template>

<script>
import CardFan from './CardFan.vue'

export default {
  name: 'DraftPanel',
  components: { CardFan },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    actions: { type: Object, default: () => ({}) }
  },
  computed: {
    draftHand() {
      return (this.state.draft && this.state.draft.hand && this.state.draft.hand[this.mySeat]) || []
    },
    picked() {
      return ((this.state.draft && this.state.draft.picked) || []).includes(this.mySeat)
    },
    myHand() {
      return ((this.state.players && this.state.players[this.mySeat]) || {}).hand || []
    }
  },
  methods: {
    pick(cid) {
      this.$emit('command', { type: 'pick_draft', seat: this.mySeat, card_id: cid })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff; border: 1px solid #e5e5e5; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; overflow: visible; }
.hint { color: #888; }
.mine { margin-top: 0.8rem; }
.mine h4 { color: #666; margin: 0 0 0.4rem; }
</style>
