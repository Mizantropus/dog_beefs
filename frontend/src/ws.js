// WebSocket-клиент партии: подписка на снапшоты + отправка команд.
export function connectGame(gameId, token, handlers = {}) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${proto}://${location.host}/ws/games/${gameId}?token=${encodeURIComponent(token)}`
  const ws = new WebSocket(url)
  ws.onmessage = (ev) => {
    let msg
    try { msg = JSON.parse(ev.data) } catch (e) { return }
    const h = handlers[msg.type]
    if (h) h(msg)
  }
  ws.onclose = (ev) => handlers.close && handlers.close(ev)
  ws.onerror = () => handlers.error && handlers.error({ detail: 'Ошибка соединения' })
  return ws
}

export function sendCommand(ws, command) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'command', command }))
  }
}