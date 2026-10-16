<template>
  <div class="backdrop" @click.self="$emit('close')">
    <div class="modal">
      <h3>{{ title }}</h3>
      <p v-if="costText" class="cost">Стоимость: {{ costText }}</p>

      <label v-if="needsTargetDistrict" class="param">
        <span>Куда (район)</span>
        <select v-model="targetDistrict">
          <option v-for="o in targetDistrictOptions" :key="o.value" :value="o.value">{{ o.text }}</option>
        </select>
      </label>

      <label v-if="needsTargetSeat" class="param">
        <span>На кого</span>
        <select v-model="targetSeat">
          <option v-for="o in playerOptions" :key="o.value" :value="o.value">{{ o.text }}</option>
        </select>
      </label>

      <label v-if="needsBuyDiscard" class="param">
        <span>Что купить</span>
        <select v-model="buyDiscard">
          <option :value="false">Взрывчатка (600$)</option>
          <option :value="true">Карта из сброса (1000$)</option>
        </select>
      </label>

      <div class="btns">
        <button class="ghost" @click="$emit('close')">Отмена</button>
        <button class="primary" @click="use">Использовать</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ABILITY_TITLES } from '../abilities'

export default {
  name: 'AbilityModal',
  props: {
    state: { type: Object, required: true },
    districtId: { type: [String, Number], required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) },
    commandType: { type: String, default: 'use_ability' }
  },
  data() {
    return { targetDistrict: null, targetSeat: null, buyDiscard: false }
  },
  computed: {
    ability() {
      return (this.state.districts[this.districtId] || {}).ability || {}
    },
    kind() {
      return this.ability.kind
    },
    title() {
      return ABILITY_TITLES[this.kind] || 'Свойство'
    },
    needsTargetDistrict() {
      return this.kind === 'spawn_mangy'
    },
    needsTargetSeat() {
      return this.kind === 'buy_kompromat'
    },
    needsBuyDiscard() {
      return this.kind === 'buy_explosive_or_discard'
    },
    costText() {
      if (this.ability.cost != null) return this.ability.cost + '$'
      if (this.kind === 'buy_explosive_or_discard') return '600$ или 1000$'
      return ''
    },
    targetDistrictOptions() {
      const id = Number(this.districtId)
      const opts = [{ value: id, text: this.name(id) }]
      for (const n of this.neighbors(id)) {
        opts.push({ value: n, text: this.name(n) })
      }
      return opts
    },
    playerOptions() {
      return (this.state.players || []).map((p) => ({ value: p.seat, text: p.name || ('Игрок ' + (p.seat + 1)) }))
    }
  },
  created() {
    this.targetDistrict = Number(this.districtId)
  },
  methods: {
    name(id) {
      return (this.districts[id] && this.districts[id].name) ? (id + '·' + this.districts[id].name) : ('Район ' + id)
    },
    neighbors(id) {
      return (this.state.edges || [])
        .filter((e) => e.a === id || e.b === id)
        .map((e) => (e.a === id ? e.b : e.a))
    },
    use() {
      this.$emit('command', {
        type: this.commandType,
        seat: this.mySeat,
        district_id: this.districtId,
        target_seat: this.targetSeat,
        buy_discard: this.buyDiscard,
        target_district: this.targetDistrict
      })
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.modal { width: 22rem; }
.cost { color: #888; }
.param { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin: 0.5rem 0; }
.param select { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
.btns { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
.btns button { flex: 1; border: none; border-radius: 0.5rem; padding: 0.55rem; cursor: pointer; }
.ghost { background: #f2f2f2; }
.primary { background: #2f6fed; color: #fff; }
</style>