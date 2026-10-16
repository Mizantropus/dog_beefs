<template>
  <div v-if="pending" class="choice panel">
    <h3>{{ title }}</h3>
    <div class="opts">
      <button v-for="o in options" :key="o.key" @click="choose(o.value)">{{ o.text }}</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChoicePanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  computed: {
    pending() {
      const pc = this.state.pending_choice
      return pc && pc.seat === this.mySeat ? pc : null
    },
    title() {
      if (!this.pending) return ''
      if (this.pending.kind === 'repair_bridge') return 'Выберите мост для ремонта'
      if (this.pending.kind === 'combat_extract') return 'Жетон «Выбить» — выберите действие'
      return 'Выберите мост для разрушения'
    },
    options() {
      if (!this.pending) return []
      return (this.pending.options || []).map((v) => {
        let value, text
        if (v && typeof v === 'object' && v.key != null) {
          value = v.key
          text = v.text || v.key
        } else if (Array.isArray(v)) {
          value = v
          text = this.name(v[0]) + ' — ' + this.name(v[1])
        } else {
          value = v
          text = String(v)
        }
        return { value: value, text: text, key: JSON.stringify(value) }
      })
    }
  },
  methods: {
    name(id) {
      return (this.districts[id] && this.districts[id].name) ? (id + '·' + this.districts[id].name) : ('Район ' + id)
    },
    choose(value) {
      this.$emit('command', { type: 'resolve_choice', seat: this.mySeat, value: value })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.opts { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }
.opts button { border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.5rem 0.8rem; cursor: pointer; background: #fafafa; }
.opts button:hover { border-color: #2f6fed; background: #eef4ff; }
</style>
