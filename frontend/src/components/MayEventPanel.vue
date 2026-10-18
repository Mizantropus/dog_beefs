<template>
  <div v-if="pending && !done" class="may panel">
    <div class="ehead">
      <img v-if="def.id != null" :src="eventCardImage(def.id)" class="eimg" :alt="def.title" />
      <div class="emeta">
        <h3>{{ def.title || 'Событие' }}</h3>
        <p class="text">{{ def.text }}</p>
      </div>
    </div>

    <div v-if="slug === 'kredit'" class="btns">
      <button class="primary" :disabled="acted" @click="act({})">Взять кредит 1000$</button>
    </div>

    <div v-else-if="slug === 'cherny_rynok_kompromata'" class="form">
      <select v-model="targetSeat">
        <option v-for="s in otherSeats" :key="s" :value="s">{{ pname(s) }}</option>
      </select>
      <input v-model.number="count" type="number" min="1" />
      <button class="primary" @click="act({ target_seat: targetSeat, count: count })">Купить (по 600$)</button>
    </div>

    <div v-else-if="slug === 'subbotnik'" class="form">
      <select v-model="districtId">
        <option v-for="d in subbotnikDistricts" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <select v-model="resource">
        <option value="money">Деньги</option>
        <option value="explosive">Взрывчатка</option>
        <option value="kompromat">Чужой компромат</option>
      </select>
      <button class="primary" @click="act({ district_id: districtId, resource: resource })">Подобрать</button>
    </div>

    <div v-else-if="slug === 'mobilizatsiya'" class="form">
      <select v-model="districtId">
        <option v-for="d in myDogDistricts" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <button class="primary" :disabled="acted" @click="act({ district_id: districtId })">Отдать пса</button>
    </div>

    <div v-else-if="slug === 'chernaya_pyatnitsa'" class="form">
      <select v-model="choice">
        <option v-for="o in blackFridayOptions" :key="o.value" :value="o.value">{{ o.text }} ({{ o.cost }}$)</option>
      </select>
      <select v-if="choice === 'kompromat'" v-model="targetSeat">
        <option v-for="s in otherSeats" :key="s" :value="s">{{ pname(s) }}</option>
      </select>
      <select v-if="choice === 'mangy'" v-model="districtId">
        <option v-for="d in mangyDistricts" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <select v-if="choice === 'dog'" v-model="districtId">
        <option v-for="d in dogDistricts" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <button class="primary" :disabled="acted" @click="act({ choice: choice, target_seat: targetSeat, district_id: districtId })">Купить</button>
    </div>

    <div v-else-if="slug === 'stroitelny_bum'" class="form">
      <select v-model="districtId">
        <option v-for="d in buildDistricts" :key="d.value" :value="d.value">{{ d.text }}</option>
      </select>
      <button class="primary" @click="act({ district_id: districtId })">Построить (скидка 300$)</button>
    </div>

    <button class="done" @click="markDone">Готово</button>
  </div>
</template>

<script>
import { eventCardImage } from '../assets'

export default {
  name: 'MayEventPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    districts: { type: Object, default: () => ({}) },
    events: { type: Object, default: () => ({}) }
  },
  data() {
    return { targetSeat: null, count: 1, districtId: null, resource: 'money', choice: null }
  },
  computed: {
    pending() { return this.state.pending_may_event || null },
    slug() { return this.pending ? this.pending.slug : '' },
    def() { return this.pending ? (this.events[this.pending.slug] || {}) : {} },
    done() { return this.pending ? (this.pending.done || []).includes(this.mySeat) : true },
    acted() { return this.pending ? (this.pending.acted || []).includes(this.mySeat) : false },
    otherSeats() {
      const out = []
      for (let s = 0; s < (this.state.player_count || 0); s++) if (s !== this.mySeat) out.push(s)
      return out
    },
    subbotnikDistricts() {
      return (this.state.board_districts || []).filter((id) => this.subbotnikEligible(id)).map((id) => ({ value: id, text: this.name(id) }))
    },
    buildDistricts() {
      return (this.state.board_districts || []).filter((id) => {
        const d = this.state.districts[id] || {}
        return d.building_owner == null && this.controller(id) === this.mySeat
      }).map((id) => ({ value: id, text: this.name(id) }))
    },
    blackFridayOptions() {
      const kinds = this.myKinds
      const opts = []
      if (kinds.has('spawn_mangy')) opts.push({ value: 'mangy', text: 'Шелудивый', cost: 0 })
      if (kinds.has('spawn_dog')) opts.push({ value: 'dog', text: 'Пёс', cost: 100 })
      if (kinds.has('buy_explosive_or_discard')) opts.push({ value: 'explosive', text: 'Взрывчатка', cost: 400 })
      if (kinds.has('buy_kompromat')) opts.push({ value: 'kompromat', text: 'Компромат', cost: 600 })
      return opts
    },
    myKinds() {
      const kinds = new Set()
      for (const id of Object.keys(this.state.districts || {})) {
        const d = this.state.districts[id]
        if (d.building_owner === this.mySeat && d.ability) kinds.add(d.ability.kind)
      }
      return kinds
    },
    myDogDistricts() {
      return (this.state.board_districts || []).filter((id) => {
        const d = this.state.districts[id] || {}
        return (d.dogs || {})[this.mySeat] > 0
      }).map((id) => ({ value: id, text: this.name(id) }))
    },
    mangyDistricts() { return this.buildingNeighborDistricts('spawn_mangy') },
    dogDistricts() { return this.buildingNeighborDistricts('spawn_dog') },
    buildingNeighborDistricts(kind) {
      const b = this.buildingDistrict(kind)
      if (b == null) return []
      const out = [b]
      for (const e of (this.state.edges || [])) {
        if (e.a === b && out.indexOf(e.b) < 0) out.push(e.b)
        if (e.b === b && out.indexOf(e.a) < 0) out.push(e.a)
      }
      return out.filter((id) => (this.state.board_districts || []).indexOf(id) >= 0).map((id) => ({ value: id, text: this.name(id) }))
    },
    buildingDistrict(kind) {
      for (const id of Object.keys(this.state.districts || {})) {
        const d = this.state.districts[id]
        if (d.building_owner === this.mySeat && d.ability && d.ability.kind === kind) return Number(id)
      }
      return null
    }
  },
  methods: {
    pname(seat) {
      const p = (this.state.players || [])[Number(seat)]
      return (p && p.name) || ('Игрок ' + (Number(seat) + 1))
    },
    eventCardImage,
    name(id) {
      return (this.districts[id] && this.districts[id].name) ? (id + '·' + this.districts[id].name) : ('Район ' + id)
    },
    controller(id) {
      const d = this.state.districts[id] || {}
      const dogs = d.dogs || {}
      const vals = {}
      for (let s = 0; s < (this.state.player_count || 0); s++) vals[s] = (dogs[s] || 0) + (d.building_owner === s ? 1 : 0)
      const mangy = d.mangy || 0
      let top = mangy
      for (const s of Object.keys(vals)) top = Math.max(top, vals[s])
      if (top === 0) return null
      const holders = Object.keys(vals).filter((s) => vals[s] === top)
      if (holders.length !== 1 || mangy === top) return null
      return Number(holders[0])
    },
    subbotnikEligible(id) {
      const d = this.state.districts[id] || {}
      const dogs = d.dogs || {}
      if ((dogs[this.mySeat] || 0) < 1) return false
      if (this.controller(id) === this.mySeat) return true
      for (const s of Object.keys(dogs)) {
        if (Number(s) !== this.mySeat && dogs[s] > 0) return false
      }
      if (d.building_owner != null && d.building_owner !== this.mySeat) return false
      return true
    },
    act(payload) {
      this.$emit('command', { type: 'may_event', action: 'act', seat: this.mySeat, ...payload })
    },
    markDone() {
      this.$emit('command', { type: 'may_event', action: 'done', seat: this.mySeat })
    }
  }
}
</script>

<style scoped>
.panel { background: #fff6e6; border: 1px solid #e8c97a; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.ehead { display: flex; gap: 0.7rem; align-items: flex-start; }
.eimg { width: 110px; border-radius: 0.5rem; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2); flex-shrink: 0; }
.emeta { flex: 1; }
.text { color: #6b5620; margin: 0.4rem 0; white-space: pre-line; }
.form { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin: 0.5rem 0; }
.form select, .form input { padding: 0.4rem; border: 1px solid #ddd; border-radius: 0.4rem; }
.btns { display: flex; gap: 0.6rem; margin-top: 0.5rem; }
button { border: none; border-radius: 0.5rem; padding: 0.5rem 0.9rem; cursor: pointer; background: #f2f2f2; }
button.primary { background: #2f6fed; color: #fff; }
button.primary:disabled { opacity: 0.5; cursor: default; }
button.done { background: #2f6fed; color: #fff; margin-top: 0.7rem; }
</style>
