<template>
  <div v-if="pending" class="mc panel">
    <h3>Проход запрещён — выберите новый район</h3>
    <div class="form">
      <select v-model="toDistrict">
        <option :value="null">Остаться</option>
        <option v-for="d in toOptions" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <button class="primary" @click="submit">Подтвердить</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MoveChoicePanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  data() {
    return { toDistrict: null }
  },
  computed: {
    pending() {
      const pc = this.state.pending_move_choice
      return pc && pc.seat === this.mySeat ? pc : null
    },
    toOptions() {
      if (!this.pending) return []
      const from = this.pending.from_district
      const out = []
      for (const e of (this.state.edges || [])) {
        if (e.a === from && e.b !== this.pending.excluded_to && this.passable(e.a, e.b) && out.indexOf(e.b) < 0) out.push(e.b)
        if (e.b === from && e.a !== this.pending.excluded_to && this.passable(e.a, e.b) && out.indexOf(e.a) < 0) out.push(e.a)
      }
      return out.filter((id) => (this.state.board_districts || []).indexOf(id) >= 0).map((id) => ({ value: id, text: this.name(id) }))
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
      this.$emit('command', { type: 'resolve_move_choice', seat: this.mySeat, to_district: this.toDistrict })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.form { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-top: 0.5rem; }
.form select { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
button.primary { background: #2f6fed; color: #fff; border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; }
</style>
