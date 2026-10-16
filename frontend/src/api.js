// Клиент REST API бэкенда + хранение токена игрока (localStorage).
const TOKEN_KEY = 'st_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function api(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  return fetch('/api' + path, { ...options, headers }).then(async (r) => {
    const data = await r.json().catch(() => ({}))
    if (!r.ok) {
      const err = new Error(data.detail || ('Ошибка ' + r.status))
      err.status = r.status
      throw err
    }
    return data
  })
}