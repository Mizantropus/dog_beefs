// Ситуативные реакции: триггеры, допустимые действия, проверка права ответа.
export const TRIGGER_LABELS = {
  combat_started: 'Начало боя',
  moved_into: 'Вход в район',
  dog_killed: 'Гибель пса',
  combat_ended: 'Конец боя',
  influence_gained: 'Получение влияния',
  roll: 'Бросок кубика'
}

export const TRIGGER_ACTIONS = {
  combat_started: ['first_strike'],
  moved_into: ['ambush', 'no_entry', 'detonate'],
  dog_killed: ['armor'],
  combat_ended: ['cleanup'],
  influence_gained: ['subsidy'],
  roll: ['reroll']
}

export const CARD_OPTIONS = {
  ambush_first_strike: ['ambush', 'first_strike'],
  subsidy_cleanup: ['subsidy', 'cleanup']
}

export function cardActionKeys(sk) {
  return CARD_OPTIONS[sk] || [sk]
}

export const SITUATIONAL_LABELS = {
  ambush: 'Засада',
  first_strike: 'Первый удар',
  subsidy: 'Субсидия',
  cleanup: 'Уборка мусора',
  reroll: 'Перебросить кубик',
  armor: 'Броник',
  no_entry: 'Проход запрещён',
  detonate: 'Активировать бомбу'
}

// Могу ли я ответить на текущее окно реакции (зеркалит серверную reactions.eligible).
export function amIEligible(state, mySeat) {
  const pr = state.pending_reaction
  if (!pr) return false
  if ((pr.responded || []).includes(mySeat)) return false
  const t = pr.trigger
  if (t === 'combat_started') return mySeat === pr.defender
  if (t === 'moved_into') {
    const d = state.districts[pr.to_district] || {}
    if (mySeat === pr.mover) return false
    const dogs = d.dogs || {}
    const hasMine = (d.explosives || []).some((e) => e.owner === mySeat)
    return (dogs[mySeat] || 0) > 0 || hasMine
  }
  if (t === 'dog_killed') return mySeat === pr.seat
  if (t === 'combat_ended') {
    const d = state.districts[pr.district_id] || {}
    const dogs = d.dogs || {}
    return (dogs[mySeat] || 0) > 0 || d.building_owner === mySeat
  }
  if (t === 'influence_gained') return mySeat !== pr.seat
  if (t === 'roll') return mySeat === pr.seat
  return false
}