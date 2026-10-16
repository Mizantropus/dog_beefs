<template>
  <div class="players">
    <div
      v-for="p in orderedPlayers"
      :key="p.seat"
      class="player"
      :class="{ active: state.phase !== 'draft' && state.current_seat === p.seat }"
      @click="$emit('view-board', p.seat)"
    >
      <span class="dot" :style="{ background: color(p.seat) }"></span>
      <div class="info">
        <strong>
          {{ p.name || ('Игрок ' + (p.seat + 1)) }}<span v-if="p.seat === mySeat"> (вы)</span>
          <span v-if="state.phase !== 'draft' && state.current_seat === p.seat" class="turn-now">● ходит</span>
        </strong>
        <span class="res">
          <span class="money">{{ p.money }}$</span>
          <span class="rgroup">
            <img :src="smallBombImage()" class="ico" alt="Взрывчатка" />
            <span class="rcount">{{ p.explosives }}</span>
          </span>
          <span v-if="p.kompromat.length" class="rgroup">
            <img v-for="(t, i) in p.kompromat" :key="'c' + i" :src="smallCompImage(t)" class="ico" :alt="'Компромат на ' + pname(t)" :title="'Компромат на ' + pname(t)" />
          </span>
          <span class="rgroup">
            <img :src="smallPoImage()" class="ico" alt="ПО" />
            <span class="rcount">{{ p.victory_points }} ПО</span>
          </span>
        </span>
        <span class="hand">Карт: {{ p.hand.length }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { PLAYER_COLORS } from '../board'
import { smallBombImage, smallCompImage, smallPoImage } from '../assets'

export default {
  name: 'PlayersPanel',
  props: {
    state: { type: Object, required: true },
    mySeat: { type: Number, default: 0 }
  },
  computed: {
    orderedPlayers() {
      const list = (this.state.players || []).slice()
      const idx = list.findIndex((p) => p.seat === this.mySeat)
      if (idx > 0) {
        const me = list.splice(idx, 1)[0]
        list.unshift(me)
      }
      return list
    }
  },
  methods: {
    pname(seat) {
      const p = (this.state.players || [])[Number(seat)]
      return (p && p.name) || ('Игрок ' + (Number(seat) + 1))
    },
    smallBombImage,
    smallCompImage,
    smallPoImage,
    color(seat) {
      return PLAYER_COLORS[seat] || '#999'
    }
  }
}
</script>

<style scoped>
.players {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1rem;
}
.player { cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 0.6rem;
  padding: 0.5rem 0.75rem;
}
.player.active { border-color: #2f6fed; background: #eef4ff; }
.dot { width: 0.9rem; height: 0.9rem; border-radius: 50%; flex: none; }
.info { display: flex; flex-direction: column; line-height: 1.3; }
.info strong {
  margin-bottom: 4px;
}
.res { color: #333; font-size: 0.9rem; display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin-bottom: 5px;}
.money { font-size: 1rem; font-weight: 600; color: #1a1a1a; }
.rgroup { display: inline-flex; align-items: center; gap: 0.15rem; }
.ico { height: 1.25rem; width: auto; display: block; }
.rcount { font-weight: 600; }
.turn-now { color: #2f6fed; font-weight: 700; animation: pulse 1.6s ease-in-out infinite; }
.hand { color: #999; font-size: 0.8rem; }
</style>