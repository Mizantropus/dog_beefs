<template>
  <div class="backdrop" @click.self="$emit('close')">
    <div class="modal">
      <h3>Колода сброса ({{ discard.length }})</h3>
      <div class="cards">
        <img v-for="(cid, i) in discardTop" :key="cid + '-' + i" :src="actionCardImage(cid)" class="card-img" :alt="title(cid)" :title="title(cid)" />
      </div>
      <p v-if="!discard.length" class="hint">Колода сброса пуста.</p>
      <button class="ghost" @click="$emit('close')">Закрыть</button>
    </div>
  </div>
</template>

<script>
import { actionCardImage } from '../assets'

export default {
  name: 'DiscardModal',
  props: {
    state: { type: Object, required: true },
    actions: { type: Object, default: () => ({}) }
  },
  computed: {
    discard() {
      return (this.state.action_deck && this.state.action_deck.discard) || []
    },
    discardTop() {
      return this.discard.slice().reverse()
    }
  },
  methods: {
    actionCardImage,
    title(cid) {
      const c = this.state.cards[cid] || {}
      const def = this.actions[c.standard_key]
      return (def && def.title) || String(cid)
    }
  }
}
</script>

<style scoped>
.modal { width: fit-content; max-width: 92vw; }
.cards { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem; margin: 0.5rem 0; }
.card-img { width: 150px; border-radius: 0.4rem; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2); }
.card { min-width: 7rem; border: 1px solid #cfcfcf; border-radius: 0.5rem; padding: 0.5rem; background: #fafafa; }
.ctitle { font-weight: 600; font-size: 0.9rem; }
.hint { color: #888; }
.ghost { border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; background: #f2f2f2; margin-top: 0.5rem; }
</style>
