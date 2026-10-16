<template>
  <div id="app">
    <Game v-if="gameId" :game-id="gameId" :token="token" @exit="onExit" />
    <Lobby v-else @started="onStarted" />
  </div>
</template>

<script>
import Lobby from './components/Lobby.vue'
import Game from './components/Game.vue'
import { getToken } from './api'

export default {
  name: 'App',
  components: { Lobby, Game },
  data() {
    return { gameId: localStorage.getItem('st_game') || '' }
  },
  computed: {
    token() {
      return getToken()
    }
  },
  methods: {
    onStarted(id) {
      this.gameId = id
    },
    onExit() {
      this.gameId = ''
    }
  }
}
</script>

<style>
#app { min-height: 100vh; }
</style>