<template>
  <div class="backdrop" @click.self="$emit('close')">
    <div class="modal">
      <h3>{{ title }}</h3>

      <!-- выбор поддействия -->
      <div v-if="options.length" class="opts">
        <button
          v-for="o in options"
          :key="o.key"
          :class="{ active: option === o.key }"
          @click="select(o)"
        >{{ o.title }}</button>
      </div>

      <!-- параметры -->
      <div v-if="visibleParams.length" class="params">
        <label v-for="p in visibleParams" :key="p" class="param">
          <span class="plabel">{{ label(p) }}</span>
          <select v-if="p === 'district_id'" v-model="values[p]">
            <option v-for="d in districtOptions('district_id')" :key="d.value" :value="d.value">{{ d.text }}</option>
          </select>
          <select v-else-if="p === 'to_district'" v-model="values[p]">
            <option value="" disabled>— куда —</option>
            <option v-for="d in districtOptions('to_district')" :key="d.value" :value="d.value">{{ d.text }}</option>
          </select>
          <select v-else-if="p === 'resource'" v-model="values[p]">
            <option v-for="r in resources" :key="r.value" :value="r.value">{{ r.text }}</option>
          </select>
          <select v-else-if="p === 'target_seat' || p === 'defender'" v-model="values[p]">
            <option value="" disabled>{{ p === 'defender' ? '— выберите —' : '— игрок —' }}</option>
            <option v-for="pl in playerOptions(p)" :key="pl.value" :value="pl.value">{{ pl.text }}</option>
          </select>
          <input v-else-if="p === 'active'" type="checkbox" v-model="values[p]" />
          <input v-else type="number" min="0" :max="maxFor(p)" v-model.number="values[p]" />
        </label>
      </div>

      <div class="btns">
        <button class="ghost" @click="$emit('close')">Отмена</button>
        <button class="discard" @click="discard">Сбросить за 100$</button>
        <button class="primary" :disabled="!canPlay" @click="play">Сыграть</button>
      </div>
    </div>
  </div>
</template>

<script>
import { paramsFor, PARAM_LABELS, RESOURCES } from '../actions'

export default {
  name: 'CardPlayModal',
  props: {
    state: { type: Object, required: true },
    cardId: { type: [String, Number], required: true },
    mySeat: { type: Number, required: true },
    actions: { type: Object, default: () => ({}) },
    districts: { type: Object, default: () => ({}) }
  },
  data() {
    return { option: null, values: {}, resources: RESOURCES }
  },
  computed: {
    card() {
      return this.state.cards[this.cardId] || {}
    },
    def() {
      return this.actions[this.card.standard_key] || {}
    },
    title() {
      return this.def.title || 'Карта'
    },
    options() {
      return this.def.options || []
    },
    standardKey() {
      return this.card.standard_key
    },
    paramDefs() {
      return paramsFor(this.standardKey, this.option)
    },
    canPlay() {
      if (this.standardKey === 'start_fight') {
        return this.values.defender !== '' && this.values.defender != null
      }
      return true
    },
    visibleParams() {
      return this.paramDefs.filter((p) => {
        if (p === 'target_seat') {
          const sk = this.standardKey
          const opt = this.option
          if (sk === 'lift_place' && (opt === 'take_resource' || opt === 'place_resource')) {
            return this.values.resource === 'kompromat'
          }
        }
        return true
      })
    }
  },
  created() {
    if (this.options.length) this.option = this.options[0].key
    this.initValues()
  },
  methods: {
    initValues() {
      const v = { active: true, resource: 'money', dogs_count: 0, mangy_count: 0 }
      for (const p of this.paramDefs) {
        if (!(p in v)) {
          if (p === 'district_id') {
            const opts = this.districtOptions('district_id')
            v[p] = opts.length ? opts[0].value : null
          } else {
            v[p] = ''
          }
        }
      }
      this.values = v
    },
    select(o) {
      this.option = o.key
      this.initValues()
    },
    label(p) {
      return PARAM_LABELS[p] || p
    },
    districtOptions(p) {
      const ids = (this.state.board_districts || []).filter((id) => {
        if (p === 'to_district') {
          const from = this.values.district_id
          return id !== from && this.areAdjacent(from, id) && this.isPassable(from, id)
        }
        return this.validDistrict(id)
      })
      return ids.map((id) => ({
        value: id,
        text: (this.districts[id] && this.districts[id].name) ? (id + '·' + this.districts[id].name) : ('Район ' + id)
      }))
    },
    playerOptions(p) {
      let seats = (this.state.players || []).map((pl) => pl.seat)
      if (p === 'defender') {
        const d = this.state.districts[this.values.district_id] || {}
        const dogs = d.dogs || {}
        const opts = []
        if ((d.mangy || 0) > 0) opts.push({ value: -1, text: 'Шелудивые' })
        for (const s of seats) {
          if (s !== this.mySeat && (dogs[s] || 0) > 0) opts.push({ value: s, text: 'Игрок ' + (s + 1) })
        }
        return opts
      } else if (p === 'target_seat') {
        seats = seats.filter((s) => s !== this.mySeat)
      }
      return seats.map((s) => ({ value: s, text: 'Игрок ' + (s + 1) }))
    },
    validDistrict(id) {
      const sk = this.standardKey
      const opt = this.option
      const d = this.state.districts[id] || {}
      const dogs = d.dogs || {}
      const hasDog = (dogs[this.mySeat] || 0) > 0
      const hasBuilding = d.building_owner === this.mySeat
      const hasPieces = hasDog || hasBuilding
      if (sk === 'summon_recruit') return hasPieces
      if (sk === 'lift_place') {
        if (['take_resource', 'place_resource', 'lift_kompromat', 'mine', 'demine'].indexOf(opt) >= 0) return hasDog
        return true
      }
      if (sk === 'move') return hasDog
      if (sk === 'start_fight') {
        const enemyDogs = Object.keys(dogs).some((s) => Number(s) !== this.mySeat && dogs[s] > 0)
        return hasDog && (enemyDogs || (d.mangy || 0) > 0)
      }
      if (sk === 'build_destroy') {
        if (opt === 'build') return hasDog && !hasBuilding
        if (opt === 'destroy_building') return hasDog && d.building_owner != null && d.building_owner !== this.mySeat
        if (opt === 'destroy_bridge' || opt === 'repair_bridge') return hasDog
      }
      return true
    },
    maxFor(p) {
      if (p === 'dogs_count') {
        const d = this.state.districts[this.values.district_id] || {}
        return (d.dogs && d.dogs[this.mySeat]) || 0
      }
      if (p === 'mangy_count') {
        const d = this.state.districts[this.values.district_id] || {}
        return d.mangy || 0
      }
      if (p === 'amount') {
        if (this.values.resource === 'explosive') return (this.state.players[this.mySeat] || {}).explosives || 0
        return (this.state.players[this.mySeat] || {}).money || 0
      }
      return 999999
    },
    areAdjacent(a, b) {
      return (this.state.edges || []).some((e) => (e.a === a && e.b === b) || (e.a === b && e.b === a))
    },
    isPassable(a, b) {
      const key = [Math.min(a, b), Math.max(a, b)]
      return !(this.state.broken_bridges || []).some((k) => k[0] === key[0] && k[1] === key[1])
    },
    discard() {
      this.$emit('command', { type: 'discard_card', seat: this.mySeat, card_id: this.cardId })
      this.$emit('close')
    },
    play() {
      const v = this.values
      const num = (x) => (x != null && x !== '' ? Number(x) : null)
      this.$emit('command', {
        type: 'play_card',
        seat: this.mySeat,
        card_id: this.cardId,
        option: this.option,
        district_id: num(v.district_id),
        amount: v.amount != null ? v.amount : null,
        target_seat: num(v.target_seat),
        defender: v.defender === -1 ? null : num(v.defender),
        active: !!v.active,
        resource: v.resource || null,
        to_district: num(v.to_district),
        dogs_count: v.dogs_count != null ? v.dogs_count : 0,
        mangy_count: v.mangy_count != null ? v.mangy_count : 0
      })
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.modal { width: 22rem; }
.opts { display: flex; flex-direction: column; gap: 0.4rem; margin: 0.75rem 0; }
.opts button {
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  padding: 0.5rem;
  cursor: pointer;
  background: #fafafa;
  text-align: left;
}
.opts button.active { border-color: #2f6fed; background: #eef4ff; }
.params { display: flex; flex-direction: column; gap: 0.5rem; margin: 0.5rem 0; }
.param { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.plabel { color: #555; font-size: 0.9rem; }
.param select, .param input { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
.btns { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
.btns button { flex: 1; border: none; border-radius: 0.5rem; padding: 0.55rem; cursor: pointer; }
.ghost { background: #f2f2f2; }
.primary { background: #2f6fed; color: #fff; }\n.primary:disabled { background: #b9c4d6; cursor: default; opacity: 0.7; }
.discard { background: #f0b429; color: #fff; }
</style>