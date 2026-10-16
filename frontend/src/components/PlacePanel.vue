<template>
  <div v-if="pending" class="place panel">
    <h3>{{ title }}</h3>
    <div class="form">
      <select v-model="districtId">
        <option v-for="d in districtOptions" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <select v-if="kind === 'take_resource'" v-model="resource">
        <option value="money">Деньги</option>
        <option value="explosive">Взрывчатка</option>
        <option value="kompromat">Компромат</option>
      </select>
      <button class="primary" @click="submit">Подтвердить</button>
      <button v-if="kind === 'take_resource'" class="bank" @click="takeBank">Взять 300$ из банка</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PlacePanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  data() {
    return { districtId: null, resource: 'money' }
  },
  computed: {
    pending() {
      const pc = this.state.pending_place
      return pc && pc.seat === this.mySeat ? pc : null
    },
    kind() { return this.pending ? this.pending.kind : '' },
    title() {
      if (this.kind === 'place_money') return '2 — Положить 200$ в район'
      if (this.kind === 'place_explosive') return '3 — Положить взрывчатку в район'
      return '6 — Забрать ресурс из района'
    },
    districtOptions() {
      return (this.state.board_districts || []).filter((id) => {
        const d = this.state.districts[id] || {}
        const dogs = d.dogs || {}
        if (this.kind === 'take_resource') return (dogs[this.mySeat] || 0) > 0 || d.building_owner === this.mySeat
        return (dogs[this.mySeat] || 0) > 0
      }).map((id) => ({ value: id, text: this.name(id) }))
    }
  },
  methods: {
    name(id) {
      return (this.districts[id] && this.districts[id].name) ? (id + '·' + this.districts[id].name) : ('Район ' + id)
    },
    submit() {
      this.$emit('command', { type: 'resolve_place', seat: this.mySeat, district_id: this.districtId, resource: this.kind === 'take_resource' ? this.resource : null })
    },
    takeBank() {
      this.$emit('command', { type: 'resolve_place', seat: this.mySeat, district_id: null, resource: 'none' })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.form { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; align-items: center; }
.form select { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
button.primary { background: #2f6fed; color: #fff; border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; }
button.bank { background: #f0b429; color: #fff; border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; }
</style>
