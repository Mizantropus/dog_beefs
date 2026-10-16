// Гекс-поле: осевые координаты районов (2/3/4 игрока) и перевод в пиксели.
// Координаты выведены из графа смежности (hex_edges.json) и проверены на согласованность.
export const HEX_COORDS = {
  2: { 1: [0, 0], 2: [1, 0], 3: [-1, 0], 4: [-1, 1], 5: [1, -1], 6: [0, -1], 7: [0, 1] },
  3: { 1: [0, 0], 2: [1, 0], 3: [-1, 0], 4: [0, -1], 5: [0, 1], 6: [-2, 1], 7: [1, 1], 8: [1, -1], 9: [-1, 1], 10: [1, -2] },
  4: { 1: [0, 0], 2: [1, 0], 3: [-1, 0], 4: [0, -1], 5: [1, -1], 6: [2, -1], 7: [1, 1], 8: [1, -2], 9: [-1, 1], 10: [-1, -1], 11: [-1, 2], 12: [0, 1], 13: [-2, 1] }
}

export const PLAYER_COLORS = ['#D35249', '#698DC9', '#81BC77', '#EFB94D']

// Точечные корректировки раскладки (пиксели, при size=42 и riverGap=17).
// 2 игрока — без правок (идеально).
// 3 игрока — выравниваем нижний ряд (6/7 = 9/5 по вертикали, без горизонта).
// 4 игрока — выравниваем верхний ряд (10/4/5/6) и нижний (13/9/12/7):
// концы 10/6 и 13/7 убираем от горизонтального сдвига и доводим по вертикали
// до соседей; 8 и 11 сдвигаем вместе с соседями (иначе налезают).
export const HEX_NUDGE = {
  2: {},
  3: { 6: { dx: 4.25, dy: 7.3612 }, 7: { dx: -4.25, dy: 7.3612 } },
  4: {
    10: { dx: 4.25, dy: -7.3612 },
    6: { dx: -4.25, dy: -7.3612 },
    13: { dx: 4.25, dy: 7.3612 },
    7: { dx: -4.25, dy: 7.3612 },
    8: { dx: 0, dy: -14.7224 },
    11: { dx: 0, dy: 14.7224 }
  }
}

const SQRT3 = Math.sqrt(3)

// Осевые координаты (q, r) -> центр гекса (пиксели). Размер = радиус описанной окружности.
export function hexToPixel(q, r, size) {
  return { x: size * SQRT3 * (q + r / 2), y: size * 1.5 * r }
}

// Вершины шестиугольника (pointy-top) для SVG polygon.
export function hexPoints(cx, cy, size) {
  const pts = []
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 180) * (60 * i - 30)
    pts.push(`${(cx + size * Math.cos(a)).toFixed(2)},${(cy + size * Math.sin(a)).toFixed(2)}`)
  }
  return pts.join(' ')
}
export const COMBAT_TOKEN_LABELS = {
  attack: "Атаковать",
  gop: "Гоп!",
  self_gop: "СамоГоп!",
  rob: "Грабёж",
  move_dog: "Перемещение",
  leave_trace: "Оставить улику",
  attack_r: "Атаковать",
  gop_r: "Гоп!",
  extract: "Выбить",
  kompromat_opp: "Компромат на соперника"
}
export const AUTHORITY_TOKEN_LABELS = {
  dummy: "Пустышка",
  place_money: "Положить 200$",
  place_explosive: "Положить взрывчатку",
  take_money: "Взять 200$",
  swap_card: "Поменять карту",
  take_resource: "Забрать ресурс",
  take_explosive_r: "Взять взрывчатку",
  move_r: "Перемещение",
  swap_card_r: "Поменять карту/жетон",
  take_discard_r: "Взять карту сброса"
}
export const DIE_SYMBOLS = ['🦴', '🐾', '🥣', '🏠', '🎾', '🦺']  // кость, лапа, миска, конура, мячик, ошейник
export const MANGY_FACES = ['kill_dog', 'dog_to_mangy', 'kompromat', 'recruit', 'mangy_dies', 'pay_100']
export const MANGY_FACE_LABELS = {
  kill_dog: 'Шелудивые убивают одного вашего пса',
  dog_to_mangy: 'Один ваш пёс становится шелудивым',
  kompromat: 'Компромат на вас ложится в район боя',
  recruit: 'Один шелудивый вербуется и становится вашим псом',
  mangy_dies: 'Один шелудивый погибает',
  pay_100: 'Сбросьте 100$ в банк'
}

export const AUTHORITY_TOKEN_ICONS = {
  dummy: '⬜', place_money: '💰', place_explosive: '💣', take_money: '💵', swap_card: '🔁',
  take_resource: '🎒', take_explosive_r: '💣', move_r: '➡️', swap_card_r: '🔁', take_discard_r: '🃏'
}

export const AUTHORITY_TOKEN_VALUES = {
  dummy: 1, place_money: 2, place_explosive: 3, take_money: 4, swap_card: 5, take_resource: 6,
  take_explosive_r: 3, move_r: 4, swap_card_r: 5, take_discard_r: 6
}
export const AUTHORITY_TOKEN_REWARD = {
  dummy: false, place_money: false, place_explosive: false, take_money: false, swap_card: false, take_resource: false,
  take_explosive_r: true, move_r: true, swap_card_r: true, take_discard_r: true
}

// Жетон авторитета всегда показывается со своим числовым значением: «3 — Положить взрывчатку».
export function authorityTokenLabel(key) {
  const v = AUTHORITY_TOKEN_VALUES[key]
  const name = AUTHORITY_TOKEN_LABELS[key] || key
  return v != null ? `${v} — ${name}` : name
}

export const COMBAT_TOKEN_REWARD = {
  attack: false, gop: false, self_gop: false, rob: false, move_dog: false, leave_trace: false,
  attack_r: true, gop_r: true, extract: true, kompromat_opp: true
}
export const COMBAT_TOKEN_SHORT = {
  attack: 'Атака', gop: 'Гоп', self_gop: 'СамоГоп', rob: 'Грабёж', move_dog: 'Ход', leave_trace: 'Улика',
  attack_r: 'Атака', gop_r: 'Гоп', extract: 'Выбить', kompromat_opp: 'Компр.'
}