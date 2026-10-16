<template>
  <div v-if="combat" class="combat panel">
    <h3>Бой · район {{ combat.district_id }}</h3>
    <div class="info">
      <span>⚔️ {{ playerName(combat.attacker) }}</span>
      <span v-if="combat.defender !== null">против {{ playerName(combat.defender) }}</span>
      <span v-else>против шелудивых</span>
    </div>

    <div v-if="!pending" class="btns">
      <button v-if="roller === mySeat" class="primary" @click="roll">Бросить кубик</button>
      <button v-else-if="roller === null && combat.attacker === mySeat" @click="roll">Бросок шелудивых</button>
      <p v-else class="hint">
        {{ roller === null ? 'Ход шелудивых…' : 'Ожидаем броска ' + playerName(roller) + '…' }}
      </p>
    </div>

    <div v-else-if="isMangy" class="result">
      <p class="die-line">
        Выпало: <DiceCube :key="pending.face" :face="pending.face" :faces="mangyFaces" />
        <span class="mangy-label">{{ mangyLabel }}</span>
      </p>
      <div class="btns">
        <button v-if="combat.attacker === mySeat" class="primary" @click="ackMangy">ОК</button>
        <p v-else class="hint">Ожидаем подтверждения атакующего…</p>
      </div>
    </div>

    <div v-else-if="roller === mySeat" class="result">
      <p class="die-line">
        Выпало: <DiceCube :key="pending.face" :face="pending.face" />
        <img v-if="tokenImage(roller, pending.face)" :src="tokenImage(roller, pending.face)" :title="faceLabel(roller, pending.face)" class="tok-img" />
        <span v-if="isReward(roller, pending.face)" class="badge">наградной</span>
        <span class="opp">· противоположная: <img :src="dieFaceImage(pending.opposite)" :alt="dieSymbol(pending.opposite)" class="die-img" /> <img v-if="tokenImage(roller, pending.opposite)" :src="tokenImage(roller, pending.opposite)" :title="faceLabel(roller, pending.opposite)" class="tok-img" /></span>
      </p>
      <div v-if="isMoveDog" class="move">
        <label>Кого:
          <select v-model="moveSeat">
            <option v-for="o in moveOptions" :key="o.value" :value="o.value">{{ o.text }}</option>
          </select>
        </label>
        <label>Куда:
          <select v-model="moveTo">
            <option v-for="o in moveToOptions" :key="o.value" :value="o.value">{{ o.text }}</option>
          </select>
        </label>
      </div>
      <div class="btns">
        <button class="primary" @click="resolve(false)">Принять результат</button>
        <button :disabled="!hasKompromat" @click="resolve(true)">Перевернуть (компромат)</button>
      </div>
    </div>

    <div v-else class="result">
      <p class="die-line">Против вас выпало: <DiceCube :key="pending.face" :face="pending.face" /> <img v-if="tokenImage(roller, pending.face)" :src="tokenImage(roller, pending.face)" :title="faceLabel(roller, pending.face)" class="tok-img" /></p>
      <p class="hint">Ожидаем решения атакующего…</p>
    </div>
  </div>
</template>

<script>
import { COMBAT_TOKEN_LABELS, COMBAT_TOKEN_REWARD, DIE_SYMBOLS, MANGY_FACES, MANGY_FACE_LABELS } from '../board'
import { combatTokenImage, dieFaceImage, mangyDieFaceImage } from '../assets'
import DiceCube from './DiceCube.vue'

export default {
  name: 'CombatPanel',
  components: { DiceCube },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true }
  },
  data() {
    return { moveSeat: -1, moveTo: null }
  },
  computed: {
    combat() {
      return this.state.combat
    },
    pending() {
      return this.combat ? this.combat.pending : null
    },
    isMangy() {
      return this.pending ? !!this.pending.mangy : false
    },
    mangyLabel() {
      if (!this.pending) return ''
      const name = MANGY_FACES[this.pending.face]
      return MANGY_FACE_LABELS[name] || name || ''
    },
    mangyFaces() {
      return [0, 1, 2, 3, 4, 5].map((f) => mangyDieFaceImage(f))
    },
    roller() {
      if (!this.combat) return null
      return this.combat.next_is_attacker ? this.combat.attacker : this.combat.defender
    },
    hasKompromat() {
      const p = this.state.players[this.mySeat]
      return !!(p && p.kompromat && p.kompromat.length)
    },
    isMoveDog() {
      if (!this.pending) return false
      const line = (this.state.players[this.roller] || {}).combat_line || []
      return line[this.pending.face] === 'move_dog'
    },
    moveOptions() {
      const d = this.state.districts[this.combat.district_id] || {}
      const opts = []
      const dogs = d.dogs || {}
      const seats = this.combat.defender !== null ? [this.combat.attacker, this.combat.defender] : [this.combat.attacker]
      for (const seat of seats) {
        for (let i = 0; i < (dogs[seat] || 0); i++) {
          opts.push({ value: Number(seat), text: 'Пёс ' + this.playerName(seat) })
        }
      }
      if ((d.mangy || 0) > 0) opts.push({ value: -1, text: 'Шелудивый' })
      return opts
    },
    moveToOptions() {
      return (this.state.edges || [])
        .filter((e) => e.a === this.combat.district_id || e.b === this.combat.district_id)
        .map((e) => {
          const n = e.a === this.combat.district_id ? e.b : e.a
          return { value: n, text: String(n) }
        })
    }
  },
  methods: {
    dieFaceImage,
    playerName(seat) {
      const p = (this.state.players || [])[Number(seat)]
      return (p && p.name) || ('Игрок ' + (Number(seat) + 1))
    },
    faceLabel(seat, face) {
      const line = (this.state.players[seat] || {}).combat_line || []
      return COMBAT_TOKEN_LABELS[line[face]] || 'грань ' + (Number(face) + 1)
    },
    tokenImage(seat, face) {
      const line = (this.state.players[seat] || {}).combat_line || []
      return combatTokenImage(line[face], seat)
    },
    dieSymbol(face) { return DIE_SYMBOLS[face] || '?' },
    isReward(seat, face) {
      const line = (this.state.players[seat] || {}).combat_line || []
      return !!COMBAT_TOKEN_REWARD[line[face]]
    },
    roll() {
      this.$emit('command', { type: 'roll_combat', seat: this.mySeat })
    },
    ackMangy() {
      this.$emit('command', { type: 'ack_mangy_roll', seat: this.mySeat })
    },
    resolve(flip) {
      const cmd = { type: 'resolve_combat', seat: this.mySeat, flip }
      if (this.isMoveDog) {
        cmd.move_seat = this.moveSeat === -1 ? null : this.moveSeat
        cmd.move_to = this.moveTo
      }
      this.$emit('command', cmd)
    },
  }
}
</script>

<style scoped>
.panel { background: #fff; border: 1px solid #e5e5e5; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
.info { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; color: #444; }
.btns { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.btns button {
  border: none;
  border-radius: 0.5rem;
  padding: 0.55rem 1rem;
  cursor: pointer;
  background: #f2f2f2;
  font-size: 0.95rem;
}
.btns button.primary { background: #2f6fed; color: #fff; }
.btns button:disabled { opacity: 0.5; cursor: default; }
.result p { margin: 0.4rem 0; }
.opp { color: #888; font-size: 0.9rem; }
.die { display: inline-block; font-size: 1.9rem; font-weight: 700; animation: spin 0.5s ease-out; }
.tok-img { height: 2.4rem; width: auto; vertical-align: middle; margin-right: 8px; }
.die-img { height: 2.6rem; width: auto; vertical-align: middle; }
@keyframes spin { 0% { transform: rotate(0deg) scale(0.4); opacity: 0; } 60% { transform: rotate(720deg) scale(1.15); opacity: 1; } 100% { transform: rotate(720deg) scale(1); } }
.die-line { margin: 0.4rem 0; }
.badge { display: inline-block; background: #f0b429; color: #fff; border-radius: 0.4rem; padding: 0.1rem 0.4rem; font-size: 0.75rem; margin-left: 0.3rem; }
.mangy-label { margin-left: 0.4rem; font-weight: 600; color: #555; }
.hint { color: #888; margin: 0; align-self: center; }
.move { display: flex; gap: 0.75rem; margin: 0.5rem 0; }
.move label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; }
.move select { padding: 0.35rem; border: 1px solid #ddd; border-radius: 0.4rem; }
</style>