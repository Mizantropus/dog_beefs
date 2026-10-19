<template>
  <div class="game">
    <div v-if="error" class="err-backdrop" @click.self="error = ''">
      <div class="err-modal">
        <p class="err-text">{{ error }}</p>
        <button class="err-ok" @click="error = ''">ОК</button>
      </div>
    </div>
    <div v-if="!state" class="loading">Подключаемся к партии…</div>
    <template v-else>
      <div class="topbar">
        <span class="phase-badge">{{ phaseLabel }}</span>
        <span class="round">Раунд {{ state.round }}</span>
        <div class="decks">
          <div class="deck" :title="'Колода действий (' + actionDraw.length + ')'">
            <img :src="actionCardBack()" class="deck-img" alt="Колода действий" />
            <span class="deck-count">{{ actionDraw.length }}</span>
          </div>
          <div class="deck" :title="'Колода событий (' + eventDraw.length + ')'">
            <img :src="eventCardBack()" class="deck-img" alt="Колода событий" />
            <span class="deck-count">{{ eventDraw.length }}</span>
          </div>
        </div>
        <button class="ghost" @click="showDiscard = true">Колода сброса</button>
        <button class="ghost" @click="back">Выйти</button>
      </div>
      <Board :state="state" :districts="districtMap" />
      <PlayersPanel :state="state" :my-seat="mySeat" @view-board="viewSeat = $event" />
      <PlayerBoard :state="state" :my-seat="mySeat" />

      <ReactionPanel :state="state" :my-seat="mySeat" :districts="districtMap" @command="send" />
      <InfluencePanel :state="state" :my-seat="mySeat" @command="send" />
      <KompromatPropertyPanel
        :state="state"
        :my-seat="mySeat"
        :districts="districtMap"
        @command="send"
        @use-property="openProperty"
      />
      <KompromatRollPanel :state="state" :my-seat="mySeat" @command="send" />
      <SwapPanel :state="state" :my-seat="mySeat" :actions="actionMap" @command="send" />
      <PlacePanel :state="state" :my-seat="mySeat" :districts="districtMap" @command="send" />
      <MovePanel :state="state" :my-seat="mySeat" :districts="districtMap" @command="send" />
      <MoveChoicePanel :state="state" :my-seat="mySeat" :districts="districtMap" @command="send" />
      <TokenSwapPanel :state="state" :my-seat="mySeat" @command="send" />
      <MayEventPanel :state="state" :my-seat="mySeat" :districts="districtMap" :events="eventsMap" @command="send" />
      <KazinoPanel :state="state" :my-seat="mySeat" :events="eventsMap" @command="send" />
      <ChoicePanel :state="state" :my-seat="mySeat" :districts="districtMap" @command="send" />
      <DiscardModal v-if="showDiscard" :state="state" :actions="actionMap" @close="showDiscard = false" />
      <div v-if="viewSeat !== null" class="board-modal" @click.self="viewSeat = null">
        <div class="board-modal-box">
          <PlayerBoard :state="state" :my-seat="viewSeat" :title="'Планшет — ' + pname(viewSeat)" :collapsible="false" />
          <button class="ghost" @click="viewSeat = null">Закрыть</button>
        </div>
      </div>
      <PeekPanel :state="state" :my-seat="mySeat" :events="eventsMap" @command="send" />
      <EventPanel :state="state" :my-seat="mySeat" :events="eventsMap" @command="send" />
      <EventRollPanel :state="state" :my-seat="mySeat" :events="eventsMap" @command="send" />
      <PenaltyPanel :state="state" :my-seat="mySeat" @command="send" />
      <EventExplosionPanel :state="state" :my-seat="mySeat" :districts="districtMap" :events="eventsMap" @command="send" />

      <DraftPanel
        v-if="state.phase === 'draft'"
        :state="state"
        :my-seat="mySeat"
        :actions="actionMap"
        @command="send"
      />
      <CombatPanel
        v-if="state.combat"
        :state="state"
        :my-seat="mySeat"
        @command="send"
      />
      <HandPanel
        v-if="state.phase === 'play'"
        :state="state"
        :my-seat="mySeat"
        :actions="actionMap"
        @command="send"
        @play-card="openPlay"
      />

      <AbilitiesPanel
        v-if="state.phase === 'play' && !state.combat"
        :state="state"
        :my-seat="mySeat"
        :districts="districtMap"
        @use-ability="openAbility"
      />

      <AbilityModal
        v-if="abilityDistrict"
        :state="state"
        :district-id="abilityDistrict"
        :my-seat="mySeat"
        :districts="districtMap"
        :command-type="abilityMode"
        @command="send"
        @close="abilityDistrict = null"
      />

      <CardPlayModal
        v-if="playCard"
        :state="state"
        :card-id="playCard"
        :my-seat="mySeat"
        :actions="actionMap"
        :districts="districtMap"
        @command="send"
        @close="playCard = null"
      />
    </template>
  </div>
</template>

<script>
import { api } from '../api'
import { connectGame, sendCommand } from '../ws'
import { loadActions } from '../actions'
import { actionCardBack, eventCardBack } from '../assets'
import Board from './Board.vue'
import PlayersPanel from './PlayersPanel.vue'
import PlayerBoard from './PlayerBoard.vue'
import DraftPanel from './DraftPanel.vue'
import HandPanel from './HandPanel.vue'
import CardPlayModal from './CardPlayModal.vue'
import CombatPanel from './CombatPanel.vue'
import ReactionPanel from './ReactionPanel.vue'
import InfluencePanel from './InfluencePanel.vue'
import AbilitiesPanel from './AbilitiesPanel.vue'
import AbilityModal from './AbilityModal.vue'
import KompromatPropertyPanel from './KompromatPropertyPanel.vue'
import KompromatRollPanel from './KompromatRollPanel.vue'
import SwapPanel from './SwapPanel.vue'
import PlacePanel from './PlacePanel.vue'
import MovePanel from './MovePanel.vue'
import MoveChoicePanel from './MoveChoicePanel.vue'
import TokenSwapPanel from './TokenSwapPanel.vue'
import MayEventPanel from './MayEventPanel.vue'
import KazinoPanel from './KazinoPanel.vue'
import ChoicePanel from './ChoicePanel.vue'
import DiscardModal from './DiscardModal.vue'
import EventPanel from './EventPanel.vue'
import EventRollPanel from './EventRollPanel.vue'
import PenaltyPanel from './PenaltyPanel.vue'
import EventExplosionPanel from './EventExplosionPanel.vue'
import PeekPanel from './PeekPanel.vue'

const PHASES = {
  setup: 'Подготовка',
  draft: 'Драфт карт',
  play: 'Розыгрыш',
  end_round: 'Разбор полётов',
  finished: 'Завершена'
}

export default {
  name: 'Game',
  components: { Board, PlayersPanel, PlayerBoard, DraftPanel, HandPanel, CardPlayModal, CombatPanel, ReactionPanel, InfluencePanel, AbilitiesPanel, AbilityModal, KompromatPropertyPanel, KompromatRollPanel, SwapPanel, DiscardModal, PlacePanel, MovePanel, MoveChoicePanel, TokenSwapPanel, MayEventPanel, KazinoPanel, ChoicePanel, EventPanel, EventExplosionPanel, EventRollPanel, PenaltyPanel, PeekPanel },
  props: {
    gameId: { type: String, required: true },
    token: { type: String, required: true }
  },
  data() {
    return {
      state: null,
      districtMap: {},
      actionMap: {},
      mySeat: Number(localStorage.getItem('st_seat') || 0),
      abilityDistrict: null,
      abilityMode: 'use_ability',
      eventsMap: {},
      ws: null,
      destroyed: false,
      error: '',
      playCard: null,
      viewSeat: null,
      showDiscard: false
    }
  },
  computed: {
    phaseLabel() {
      return PHASES[this.state.phase] || this.state.phase
    },
    actionDraw() { return (this.state.action_deck && this.state.action_deck.draw) || [] },
    eventDraw() { return (this.state.event_deck && this.state.event_deck.draw) || [] }
  },
  async mounted() {
    try {
      const [ds, acts, evs] = await Promise.all([
        api('/catalog/districts'),
        loadActions(),
        api('/catalog/events')
      ])
      this.districtMap = Object.fromEntries(ds.map((d) => [d.id, d]))
      this.actionMap = acts
      this.eventsMap = Object.fromEntries(evs.map((e) => [e.slug, e]))
    } catch (e) {
      // каталог не критичен для отрисовки
    }
    this.connect()
  },
  beforeDestroy() {
    this.destroyed = true
    if (this.ws) this.ws.close()
  },
  methods: {
    pname(seat) {
      const p = (this.state.players || [])[Number(seat)]
      return (p && p.name) || ('Игрок ' + (Number(seat) + 1))
    },
    actionCardBack,
    eventCardBack,
    connect() {
      if (this.destroyed) return
      this.ws = connectGame(this.gameId, this.token, {
        state: (msg) => {
          this.state = msg.state
          this.error = ''
        },
        error: (msg) => { this.error = msg.detail },
        close: () => {
          if (this.destroyed) return
          this.error = 'Соединение потеряно — переподключаемся…'
          setTimeout(() => this.connect(), 1000)
        }
      })
    },
    send(cmd) {
      this.error = ''
      sendCommand(this.ws, { ...cmd, seat: this.mySeat })
    },
    openPlay(cardId) {
      this.playCard = cardId
    },
    openAbility(districtId) {
      this.abilityDistrict = districtId
      this.abilityMode = 'use_ability'
    },
    openProperty(districtId) {
      this.abilityDistrict = districtId
      this.abilityMode = 'resolve_kompromat'
    },
    back() {
      localStorage.removeItem('st_game')
      localStorage.removeItem('st_code')
      localStorage.removeItem('st_seat')
      this.$emit('exit')
    }
  }
}
</script>

<style scoped>
.game { max-width: 60rem; margin: 0 auto; padding: 1rem; font-family: system-ui, sans-serif; }
.topbar { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.phase-badge { display: inline-block; background: #0f766e; color: #fff; border-radius: 999px; padding: 0.15rem 0.65rem; font-size: 0.8rem; font-weight: 600; }
.round { color: #888; }
.decks { display: flex; gap: 0.5rem; align-items: center; }
.deck { position: relative; display: inline-block; }
.deck-img { width: 32px; display: block; border-radius: 0.25rem; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25); }
.deck-count { position: absolute; top: -6px; right: -6px; background: #2f6fed; color: #fff; border-radius: 999px; font-size: 0.62rem; padding: 1px 5px; font-weight: 700; line-height: 1.2; }
.ghost { margin-left: auto; background: #f2f2f2; border: none; border-radius: 0.5rem; padding: 0.4rem 0.8rem; cursor: pointer; }
.loading { text-align: center; color: #888; padding: 3rem; }
.err-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 40; }
.err-modal { background: #fff; border-radius: 0.75rem; padding: 1.25rem; width: 22rem; max-width: 92vw; box-shadow: 0 10px 40px rgba(0,0,0,0.25); }
.err-text { color: #b03030; margin: 0.4rem 0 0.8rem; white-space: pre-line; }
.err-ok { width: 100%; border: none; border-radius: 0.5rem; padding: 0.55rem; cursor: pointer; background: #2f6fed; color: #fff; font-size: 1rem; }
.board-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 20; }
.board-modal-box { background: #fff; border-radius: 0.75rem; padding: 1.25rem; width: 92vw; max-width: 70rem; max-height: 94vh; overflow: auto; }
</style>