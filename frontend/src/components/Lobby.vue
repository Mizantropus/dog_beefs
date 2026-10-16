<template>
  <div class="lobby">
    <!-- Главный экран: создать комнату или войти по коду -->
    <div v-if="!roomCode" class="home">
      <h1 class="title">Собачьи тёрки</h1>
      <p class="subtitle">Онлайн-игра, в которой вы будете биться за контроль над районами города. 2–4 игрока</p>

      <div class="card">
        <h2>Ваше имя</h2>
        <input v-model="name" class="code-input name-input" placeholder="ИМЯ" maxlength="24" />
      </div>

      <div class="card">
        <h2>Создать комнату</h2>
        <div class="players">
          <label v-for="n in [2, 3, 4]" :key="n" class="chip">
            <input type="radio" :value="n" v-model="playerCount" />
            <span>{{ n }} игрока</span>
          </label>
        </div>
        <button class="primary" @click="createRoom" :disabled="busy || !name.trim()">
          {{ busy ? 'Создаём…' : 'Создать' }}
        </button>
      </div>

      <div class="card">
        <h2>Войти по коду</h2>
        <input
          v-model="joinCode"
          class="code-input"
          placeholder="КОД КОМНАТЫ"
          maxlength="6"
          @keyup.enter="joinRoom"
        />
        <button class="primary" @click="joinRoom" :disabled="busy || !joinCode || !name.trim()">
          {{ busy ? 'Входим…' : 'Войти' }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- Лобби комнаты -->
    <div v-else-if="!gameId" class="room">
      <h1 class="title">Комната</h1>
      <div class="code-big">
        <span class="code">{{ roomCode }}</span>
        <button class="ghost" @click="copyCode">{{ copied ? 'Скопировано' : 'Копировать' }}</button>
      </div>
      <p class="subtitle">Скиньте код игрокам — они войдут и займут места.</p>

      <div class="seats">
        <div
          v-for="s in playerCount"
          :key="s"
          class="seat"
          :class="{ taken: seatsTaken[s - 1], you: seat === s - 1 }"
        >
          <span class="num">{{ seatName(s - 1) || ('Место ' + s) }}</span>
          <span class="state">{{ seatsTaken[s - 1] ? (seat === s - 1 ? 'Вы' : 'Занято') : 'Свободно' }}</span>
        </div>
      </div>

      <button v-if="seat === 0" class="primary start" @click="startGame" :disabled="busy || !full">
        {{ busy ? 'Стартуем…' : 'Начать игру' }}
      </button>
      <p v-else class="hint">{{ full ? 'Ожидаем решения хоста…' : 'Ожидаем игроков…' }}</p>

      <button class="ghost leave" @click="leave">Покинуть комнату</button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- Игра началась (заглушка до части 3.2) -->
    <div v-else class="started">
      <h1 class="title">Игра началась!</h1>
      <p>Номер партии: <code>{{ gameId }}</code></p>
      <p class="subtitle">Игровое поле появится в части 3.2.</p>
    </div>
  </div>
</template>

<script>
import { api, getToken, setToken } from '../api'

export default {
  name: 'Lobby',
  data() {
    return {
      playerCount: 2,
      name: localStorage.getItem('st_name') || '',
      joinCode: '',
      roomCode: localStorage.getItem('st_code') || '',
      seat: Number(localStorage.getItem('st_seat') || 0),
      seatsTaken: [],
      names: [],
      gameId: localStorage.getItem('st_game') || '',
      busy: false,
      error: '',
      copied: false,
      pollTimer: null
    }
  },
  computed: {
    full() {
      return this.seatsTaken.length > 0 && this.seatsTaken.every(Boolean)
    }
  },
  created() {
    if (this.roomCode && getToken() && !this.gameId) {
      this.startPolling()
    }
  },
  beforeDestroy() {
    this.stopPolling()
  },
  methods: {
    startPolling() {
      this.stopPolling()
      this.pollRoom()
      this.pollTimer = setInterval(this.pollRoom, 2000)
    },
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
    async createRoom() {
      this.busy = true
      this.error = ''
      try {
        const r = await api('/rooms', {
          method: 'POST',
          body: JSON.stringify({ player_count: this.playerCount, name: this.name.trim() })
        })
        this.enterRoom(r)
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    },
    async joinRoom() {
      if (!this.joinCode.trim()) return
      this.busy = true
      this.error = ''
      try {
        const r = await api(`/rooms/${this.joinCode.trim().toUpperCase()}/join`, { method: 'POST', body: JSON.stringify({ name: this.name.trim() }) })
        this.enterRoom(r)
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    },
    enterRoom(r) {
      setToken(r.token)
      localStorage.setItem('st_name', this.name.trim())
      localStorage.setItem('st_code', r.code)
      localStorage.setItem('st_seat', String(r.seat))
      this.roomCode = r.code
      this.seat = r.seat
      this.startPolling()
    },
    async pollRoom() {
      if (!this.roomCode) return
      try {
        const room = await api(`/rooms/${this.roomCode}`)
        this.seatsTaken = room.seats_taken
        this.playerCount = room.player_count
        this.names = room.names || []
        if (room.game_id) {
          this.gameId = room.game_id
          localStorage.setItem('st_game', room.game_id)
          this.stopPolling()
          this.$emit('started', this.gameId)
        }
      } catch (e) {
        // комната могла исчезнуть — молча пропускаем
      }
    },
    async startGame() {
      this.busy = true
      this.error = ''
      try {
        const r = await api(`/rooms/${this.roomCode}/start`, {
          method: 'POST',
          headers: { 'X-Player-Token': getToken() }
        })
        this.gameId = r.game_id
        localStorage.setItem('st_game', r.game_id)
        this.stopPolling()
        this.$emit('started', this.gameId)
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    },
    seatName(seat) {
      return (this.names && this.names[seat]) || ''
    },
    copyCode() {
      navigator.clipboard.writeText(this.roomCode).then(() => {
        this.copied = true
        setTimeout(() => (this.copied = false), 1500)
      })
    },
    leave() {
      this.stopPolling()
      localStorage.removeItem('st_code')
      localStorage.removeItem('st_seat')
      localStorage.removeItem('st_game')
      this.roomCode = ''
      this.gameId = ''
      this.seat = 0
      this.seatsTaken = []
    }
  }
}
</script>

<style scoped>
.lobby {
  max-width: 34rem;
  margin: 0 auto;
  padding: 2rem 1rem;
  font-family: system-ui, sans-serif;
}
.title { font-size: 2.2rem; margin: 0.5rem 0; text-align: center; }
.subtitle { text-align: center; color: #888; margin: 0 0 1.5rem; }
.card {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 0.75rem;
  padding: 1.25rem 1.25rem 1.5rem;
  margin-bottom: 1rem;
}
.card h2 { margin: 0 0 0.75rem; font-size: 1.1rem; }
.players { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.chip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  padding: 0.5rem;
  cursor: pointer;
}
.chip input { margin: 0; }
.code-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.6rem;
  font-size: 1.2rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  margin-bottom: 0.75rem;
}
button {
  border: none;
  border-radius: 0.5rem;
  padding: 0.65rem 1rem;
  font-size: 1rem;
  cursor: pointer;
}
button:disabled { opacity: 0.5; cursor: default; }
.primary { background: #2f6fed; color: #fff; width: 100%; }
.ghost { background: #f2f2f2; color: #333; }
.code-big { display: flex; align-items: center; justify-content: center; gap: 0.75rem; }
.code {
  font-size: 2.4rem;
  font-weight: 700;
  letter-spacing: 0.25em;
  color: #2f6fed;
}
.seats { display: grid; grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr)); gap: 0.75rem; margin: 1rem 0 1.25rem; }
.seat {
  border: 1px solid #e5e5e5;
  border-radius: 0.6rem;
  padding: 0.9rem;
  text-align: center;
  color: #aaa;
}
.seat .num { display: block; font-weight: 600; }
.seat.taken { border-color: #9bc4ff; color: #333; background: #f4f9ff; }
.seat.you { border-color: #2f6fed; color: #2f6fed; background: #eef4ff; }
.start { margin-bottom: 0.75rem; }
.hint { text-align: center; color: #888; margin-bottom: 1rem; }
.leave { width: 100%; }
.error { color: #d33; text-align: center; }
.started { text-align: center; }
</style>