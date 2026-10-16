<template>
  <div v-if="myBuildings.length" class="abilities panel">
    <h3>Свойства зданий</h3>
    <div class="list">
      <button
        v-for="d in myBuildings"
        :key="d.id"
        class="bld"
        :disabled="!canUse(d.id)"
        @click="$emit('use-ability', d.id)"
      >
        {{ name(d.id) }} — {{ title(d) }}
      </button>
    </div>
  </div>
</template>

<script>
import { ABILITY_TITLES } from '../abilities'

export default {
  name: 'AbilitiesPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  computed: {
    myBuildings() {
      const out = []
      for (const id of Object.keys(this.state.districts || {})) {
        const d = this.state.districts[id]
        if (d.building_owner === this.mySeat && d.ability && d.ability.kind) out.push(d)
      }
      return out
    },
    used() {
      return (this.state.players[this.mySeat] || {}).used_abilities || []
    },
    myTurn() {
      return this.state.current_seat === this.mySeat
    },
    playedStandard() {
      return !!((this.state.players[this.mySeat] || {}).played_standard)
    }
  },
  methods: {
    canUse(id) {
      return this.myTurn && this.playedStandard && !this.used.includes(id)
    },
    name(id) {
      return (this.districts[id] && this.districts[id].name) || id
    },
    title(d) {
      return ABILITY_TITLES[d.ability.kind] || 'свойство'
    }
  }
}
</script>

<style scoped>
.panel { background: #fff; border: 1px solid #e5e5e5; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.list { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.bld {
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  padding: 0.5rem 0.8rem;
  cursor: pointer;
  background: #fafafa;
  font-size: 0.9rem;
}
.bld:hover:not(:disabled) { border-color: #2f6fed; background: #eef4ff; }
.bld:disabled { opacity: 0.5; cursor: default; }
</style>