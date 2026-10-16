<template>
  <div class="hand panel">
    <div class="row">
      <h3>Ваша рука</h3>
      <span class="turn" :class="{ mine: myTurn }">{{ myTurn ? 'Ваш ход' : 'Ожидайте…' }}</span>
    </div>

    <CardFan
      :cards="hand"
      :state="state"
      :actions="actions"
      :clickable="myTurn && !hasPlayed"
      :dimmed="!combat && (!myTurn || hasPlayed)"
      :card-w="160"
      @pick="onPlayCard"
    />
    <p v-if="!hand.length" class="hint">Карт нет.</p>

    <div class="stash">
      <span class="stash-label">Компромат:</span>
      <span v-for="(t, i) in kompromat" :key="'k' + i" class="komp" :style="{ color: color(t) }">К</span>
      <span v-if="!kompromat.length" class="hint">нет</span>
      <select v-if="kompromat.length" v-model="discardTarget" :disabled="!myTurn || hasPlayed">
        <option v-for="t in kompromatTargets" :key="'t' + t" :value="t">
          {{ t === mySeat ? 'на себя' : 'на игрока ' + (t + 1) }}
        </option>
      </select>
    </div>

    <div v-if="!combat" class="btns">
      <button :disabled="!myTurn || hasPlayed" @click="pass">Пас</button>
      <button :disabled="!myTurn || hasPlayed || !kompromat.length" @click="playKompromat">
        Сыграть компромат
      </button>
      <button class="end" :disabled="!myTurn || !hasPlayed" @click="endTurn">Завершить ход</button>
    </div>
  </div>
</template>

<script>
import { PLAYER_COLORS } from '../board'
import CardFan from './CardFan.vue'

export default {
  name: 'HandPanel',
  components: { CardFan },
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, required: true },
    actions: { type: Object, default: () => ({}) }
  },
  data() {
    return { discardTarget: null }
  },
  computed: {
    p() { return this.state.players[this.mySeat] || {} },
    hand() { return this.p.hand || [] },
    kompromat() { return this.p.kompromat || [] },
    myTurn() { return this.state.current_seat === this.mySeat },
    hasPlayed() { return !!this.p.has_played },
    combat() { return !!this.state.combat },
    kompromatTargets() { return Array.from(new Set(this.kompromat)) }
  },
  watch: {
    kompromat() {
      if (this.discardTarget == null || this.kompromat.indexOf(this.discardTarget) < 0) {
        this.discardTarget = this.kompromat.length ? this.kompromat[0] : null
      }
    }
  },
  methods: {
    onPlayCard(cid) { this.$emit('play-card', cid) },
    endTurn() { this.$emit('command', { type: 'end_turn', seat: this.mySeat }) },
    pass() { this.$emit('command', { type: 'pass', seat: this.mySeat }) },
    playKompromat() {
      const target = this.discardTarget != null ? this.discardTarget : (this.kompromat[0] != null ? this.kompromat[0] : null)
      this.$emit('command', { type: 'play_kompromat', seat: this.mySeat, discard_target_seat: target })
    },
    color(seat) { return PLAYER_COLORS[seat] || '#999' }
  }
}
</script>

<style scoped>
.panel { background: #fff; border: 1px solid #e5e5e5; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; overflow: visible; }
.row { display: flex; align-items: center; justify-content: space-between; }
.turn { color: #888; }
.turn.mine { color: #2f6fed; font-weight: 600; animation: pulse 1.6s ease-in-out infinite; }
.btns { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.75rem; }
.btns button {
  background: #f2f2f2;
  border: none;
  border-radius: 0.5rem;
  padding: 0.55rem 1rem;
  cursor: pointer;
  font-size: 0.95rem;
}
.btns button:disabled { opacity: 0.5; cursor: default; }
.btns button.end { background: #2f6fed; color: #fff; }
.hint { color: #999; }
.stash { display: flex; align-items: center; gap: 0.4rem; margin-top: 0.5rem; flex-wrap: wrap; }
.stash-label { color: #666; font-size: 0.85rem; }
.komp { font-weight: 700; font-size: 1rem; }
.stash select { padding: 0.35rem; border: 1px solid #ddd; border-radius: 0.4rem; }
</style>
