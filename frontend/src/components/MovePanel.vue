<template>
  <div v-if="pending" class="move panel">
    <h3>4 — Перемещение (жетон авторитета)</h3>
    <div class="form">
      <select v-model="fromDistrict">
        <option v-for="d in fromOptions" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <select v-model="toDistrict">
        <option v-for="d in toOptions" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <label>Псов <input v-model.number="dogsCount" type="number" min="0" :max="maxDogs" /></label>
      <label>Шелудивых <input v-model.number="mangyCount" type="number" min="0" :max="maxMangy" /></label>
      <button class="primary" @click="submit">Переместить</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MovePanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  data() {
    return { fromDistrict: null, toDistrict: null, dogsCount: 0, mangyCount: 0 }
  },
  computed: {
    pending() {
      const pm = this.state.pending_move
      return pm && pm.seat === this.mySeat ? pm : null
    },
    fromOptions() {
      return (this.state.board_districts || []).filter((id) => {
        const d = this.state.districts[id] || {}
        return (d.dogs || {})[this.mySeat] > 0
      }).map((id) => ({ value: id, text: this.name(id) }))
    },
    toOptions() {
      if (this.fromDistrict == null) return []
      const out = []
      for (const e of (this.state.edges || [])) {
        if (e.a === this.fromDistrict && out.indexOf(e.b) < 0 && this.passable(e.a, e.b)) out.push(e.b)
        if (e.b === this.fromDistrict && out.indexOf(e.a) < 0 && this.passable(e.a, e.b)) out.push(e.a)
      }
      return out.filter((id) => (this.state.board_districts || []).indexOf(id) >= 0).map((id) => ({ value: id, text: this.name(id) }))
    },
    maxDogs() {
      if (this.fromDistrict == null) return 0
      const d = this.state.districts[this.fromDistrict] || {}
      return (d.dogs || {})[this.mySeat] || 0
    },
    maxMangy() {
      if (this.fromDistrict == null) return 0
      const d = this.state.districts[this.fromDistrict] || {}
      return d.mangy || 0
    }
  },
  methods: {
    name(id) {
      return (this.districts[id] && this.districts[id].name) ? (id + '·' + this.districts[id].name) : ('Район ' + id)
    },
    passable(a, b) {
      const key = [Math.min(a, b), Math.max(a, b)]
      return !(this.state.broken_bridges || []).some((k) => k[0] === key[0] && k[1] === key[1])
    },
    submit() {
      this.$emit('command', { type: 'resolve_move', seat: this.mySeat, from_district: this.fromDistrict, to_district: this.toDistrict, dogs_count: this.dogsCount, mangy_count: this.mangyCount })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.form { display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; margin-top: 0.5rem; }
.form select, .form input { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
.form label { color: #555; font-size: 0.9rem; }
button.primary { background: #2f6fed; color: #fff; border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; }
</style>
