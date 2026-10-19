<template>
  <div class="gamelog">
    <button class="log-toggle" :title="isOpen ? 'Скрыть журнал' : 'Показать журнал'" @click="toggle">
      <span class="toggle-arrow">{{ isOpen ? '❯' : '❮' }}</span>
      <span class="toggle-label">ЖУРНАЛ</span>
    </button>

    <transition name="slide">
      <aside v-if="isOpen" class="log-panel">
        <div class="log-head">Журнал игры</div>
        <ul class="log-list">
          <li v-for="m in moves" :key="m.id" class="log-row">
            <span class="log-time">{{ time(m.created_at) }}</span>
            <span class="log-text">{{ m.summary }}</span>
          </li>
          <li v-if="!moves.length" class="log-empty">Действий пока нет</li>
        </ul>
      </aside>
    </transition>
  </div>
</template>

<script>
import { api } from '../api'

export default {
  name: 'GameLog',
  props: {
    gameId: { type: String, required: true },
    version: { type: Number, default: 0 }
  },
  data() {
    return {
      isOpen: false,
      moves: [],
      lastFetched: 0
    }
  },
  watch: {
    version(v) {
      if (v > this.lastFetched) this.poll()
    }
  },
  mounted() {
    this.poll()
  },
  methods: {
    async poll() {
      try {
        const since = this.lastFetched
        const rows = await api('/games/' + this.gameId + '/moves?since=' + since)
        if (rows.length) {
          const newestFirst = rows.slice().reverse()
          this.moves = newestFirst.concat(this.moves)
          this.lastFetched = newestFirst[0].version
        } else {
          this.lastFetched = Math.max(this.lastFetched, this.version)
        }
      } catch (e) {
        /* игнорируем — лог не критичен */
      }
    },
    toggle() {
      this.isOpen = !this.isOpen
    },
    time(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      if (isNaN(d.getTime())) return ''
      return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    }
  }
}
</script>

<style scoped>
.gamelog { position: fixed; top: 0; right: 0; height: 100vh; z-index: 300; display: flex; align-items: stretch; }
.log-toggle {
  width: 30px;
  flex-shrink: 0;
  border: none;
  cursor: pointer;
  background: #2f6fed;
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  padding: 0.5rem 0;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.16);
}
.log-toggle .toggle-arrow { font-size: 1rem; writing-mode: horizontal-tb; }
.log-toggle .toggle-label { writing-mode: vertical-rl; text-orientation: mixed; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.16em; }
.log-panel {
  width: 320px;
  max-width: 82vw;
  height: 100vh;
  overflow: hidden;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  box-shadow: -6px 0 24px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
}
.log-head {
  padding: 0.7rem 1rem;
  border-bottom: 1px solid #eee;
  font-weight: 700;
  color: #333;
  background: #fafafa;
}
.log-list { flex: 1; overflow-y: auto; margin: 0; padding: 0.3rem 0; list-style: none; }
.log-row { display: flex; gap: 0.6rem; padding: 0.35rem 0.85rem; border-bottom: 1px solid #f2f2f2; animation: logDrop 0.28s ease-out; }
.log-time { color: #9aa0a6; font-size: 0.74rem; flex-shrink: 0; font-variant-numeric: tabular-nums; padding-top: 1px; }
.log-text { color: #333; font-size: 0.85rem; line-height: 1.35; }
.log-empty { color: #999; padding: 0.8rem 0.85rem; font-size: 0.85rem; }
@keyframes logDrop { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.slide-enter-active, .slide-leave-active { transition: width 0.24s ease, opacity 0.2s ease; }
.slide-enter, .slide-leave-to { width: 0 !important; opacity: 0; }
</style>