<template>
  <div v-if="pending" class="kprop panel">
    <h3>Белый жетон!</h3>
    <p class="hint">Можете бесплатно использовать свойство одного своего района или пропустить.</p>
    <div class="list">
      <button
        v-for="d in myBuildings"
        :key="d.id"
        class="bld"
        @click="$emit('use-property', d.id)"
      >
        {{ name(d.id) }} — {{ title(d) }}
      </button>
    </div>
    <button class="skip" @click="skip">Пропустить</button>
  </div>
</template>

<script>
import { ABILITY_TITLES } from '../abilities'

export default {
  name: 'KompromatPropertyPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  computed: {
    pending() {
      const pk = this.state.pending_kompromat
      return pk && pk.seat === this.mySeat && pk.choose ? pk : null
    },
    myBuildings() {
      const out = []
      for (const id of Object.keys(this.state.districts || {})) {
        const d = this.state.districts[id]
        if (d.building_owner === this.mySeat && d.ability && d.ability.kind) out.push(d)
      }
      return out
    }
  },
  methods: {
    name(id) {
      return (this.districts[id] && this.districts[id].name) || id
    },
    title(d) {
      return ABILITY_TITLES[d.ability.kind] || 'свойство'
    },
    skip() {
      this.$emit('command', { type: 'resolve_kompromat', seat: this.mySeat, district_id: null })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.hint { color: #8a6d3b; margin: 0.3rem 0 0.6rem; }
.list { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.6rem; }
.bld { border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.5rem 0.8rem; cursor: pointer; background: #fafafa; font-size: 0.9rem; }
.skip { border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; background: #d98e04; color: #fff; }
</style>