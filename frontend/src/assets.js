// Карта игровых изображений: семантический ключ -> URL.
// Картинки лежат в public/pictures (Vite копирует public/ в корень сборки),
// поэтому URL имеют вид /pictures/<имя файла>. Кодируем имя через
// encodeURI, чтобы пережить кириллицу и пробелы, но оставить $ литералом.

const P = (name) => `/pictures/${encodeURI(name)}`

// --- боевые жетоны: стандартные (по цвету игрока seat 0..3) ---
const COMBAT_STD = {
  attack: 'Атака',
  gop: 'Гоп',
  self_gop: 'СамоГоп',
  rob: 'Грабёж',
  move_dog: 'Перемещение-Подвинуть',
  leave_trace: 'Оставить-улику'
}

// --- боевые жетоны: наградные (без цвета игрока) ---
const COMBAT_REWARD = {
  attack_r: 'Атака-Наградной',
  gop_r: 'Гоп-Наградной',
  extract: 'Выбить-200$-или-поднять-компромат-на-себя-Наградной',
  kompromat_opp: 'Положить-компромат-на-противника-(или-взять-себе)-Наградной'
}

// --- жетоны авторитета: стандартные (по цвету игрока) ---
const AUTH_STD = {
  dummy: '1-Пустышка',
  place_money: '2-Положить-200$-в-район',
  place_explosive: '3-Положить-взрывчатку-в-район',
  take_money: '4-Взять-200$-из-банка',
  swap_card: '5-Поменять-карту-или-жетон',
  take_resource: '6-Забрать-ресурс'
}

// --- жетоны авторитета: наградные ---
const AUTH_REWARD = {
  take_explosive_r: '3-Взять-из-общего-запаса-взрывчатку-Наградной',
  move_r: '4-Перемещение-Наградной',
  swap_card_r: '5-Поменять-карту-или-жетон-(улучшенное)-Наградной',
  take_discard_r: '6-Взять-карту-из-сброса-Наградной'
}

// --- грани игрового кубика (индексы 0..5, порядок из pictures.json «Масть 1..6») ---
const DIE_FACES = ['bone', 'nose', 'dish', 'kennel', 'ball', 'collar']

// --- грани кубика шелудивых (индексы 0..5, по MANGY_FACES бэкенда) ---
// kill_dog, dog_to_mangy, kompromat, recruit, mangy_dies, pay_100
const MANGY_FACES = ['shel-6', 'shel-5', 'shel-4', 'shel-3', 'shel-2', 'shel-1']

// --- боевые жетоны ---
export function combatTokenImage(key, seat = 0) {
  if (key in COMBAT_REWARD) return P(COMBAT_REWARD[key] + '.png')
  const base = COMBAT_STD[key]
  if (!base) return null
  return P(`${base}-${seat + 1}.png`)
}

// --- жетоны авторитета ---
export function authorityTokenImage(key, seat = 0) {
  if (key in AUTH_REWARD) return P(AUTH_REWARD[key] + '.png')
  const base = AUTH_STD[key]
  if (!base) return null
  return P(`${base}-${seat + 1}.png`)
}

// --- оборот (сторона «ПО») жетона влияния ---
export function tokenBackImage(kind = 'authority', seat = 0, reward = false) {
  const base = kind === 'combat' ? 'Бой-Оборот' : 'Авторитет-Оборот'
  if (reward) return P(`${base}-Наградной.png`)
  return P(`${base}-Стандарт-${seat + 1}.png`)
}

// --- грань игрового кубика ---
export function dieFaceImage(face) {
  return P(DIE_FACES[face] + '.png')
}

// --- грань кубика шелудивых ---
export function mangyDieFaceImage(face) {
  return P(MANGY_FACES[face] + '.png')
}

// --- районы (id 1..13) и река ---
export function districtImage(id) {
  return P(`${id}-district.png`)
}
export function riverImage() {
  return P('river.png')
}
export function riverAlt1Image() {
  return P('river-alt-1.png')
}
export function riverAlt2Image() {
  return P('river-alt-2.png')
}

// --- фишки ---
export function pieceImage(kind, seat = 0) {
  if (kind === 'dog') return P(`dog-${seat + 1}.png`)
  if (kind === 'kennel') return P(`kennel-${seat + 1}.png`)
  if (kind === 'mangy') return P('shel.png')
  return null
}

// --- мосты ---
export function bridgeImage(broken = false) {
  return P(broken ? 'bridge-broken.png' : 'bridge.png')
}

// --- планшет ---
export function padImage() {
  return P('pad.png')
}

// --- компромат и бомбы ---
export function kompromatImage(seat = 0) {
  return P(`comp-${seat + 1}.png`)
}
export function bombImage(seat = null) {
  return P(seat == null ? 'bomb.png' : `bomb-${seat + 1}.png`)
}

// --- малые иконки ресурсов (панель игроков) ---
export function smallBombImage() {
  return P('small_bomb.png')
}
export function smallCompImage(seat = 0) {
  return P(`small_comp-${seat + 1}.png`)
}
export function smallPoImage() {
  return P('small_po.png')
}

// --- карты действий и событий (по номеру; сопоставление с контентом — в п.3.1) ---
export function actionCardImage(n) {
  return P(`action-${n}.png`)
}
export function actionCardBack() {
  return P('action-oborot.png')
}
export function eventCardImage(n) {
  return P(`event-${n}.png`)
}
export function eventCardBack() {
  return P('event-oborot.png')
}

export default {
  combatTokenImage,
  authorityTokenImage,
  tokenBackImage,
  dieFaceImage,
  mangyDieFaceImage,
  districtImage,
  riverImage,
  riverAlt1Image,
  riverAlt2Image,
  pieceImage,
  bridgeImage,
  padImage,
  kompromatImage,
  bombImage,
  smallBombImage,
  smallCompImage,
  smallPoImage,
  actionCardImage,
  actionCardBack,
  eventCardImage,
  eventCardBack
}
