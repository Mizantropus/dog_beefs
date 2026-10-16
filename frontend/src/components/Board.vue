<template>
  <div class="board-wrap">
    <svg :viewBox="viewBox" class="board">
      <defs>
        <linearGradient id="hex-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#f8f6ef" />
          <stop offset="100%" stop-color="#eae6d8" />
        </linearGradient>
        <clipPath v-for="id in activeDistricts" :id="'hex-clip-' + id" :key="'clip' + id">
          <polygon :points="hex(px(id), py(id))" />
        </clipPath>
      </defs>
      <!-- гексы -->
      <g v-for="id in activeDistricts" :key="id">
        <polygon :points="hex(px(id), py(id))" class="hex">
          <title>{{ districtInfo(id) }}</title>
        </polygon>
        <g :clip-path="`url(#hex-clip-${id})`">
          <image
            :href="districtImage(id)"
            :x="px(id) - size"
            :y="py(id) - size * sqrt3 / 2"
            :width="size * 2"
            :height="size * sqrt3"
            :transform="`rotate(${hexRotate}, ${px(id)}, ${py(id)})`"
            preserveAspectRatio="xMidYMid meet"
            class="dimg"
          />
        </g>
        <!-- здание -->
        <image v-if="hasBuilding(id)" :href="pieceImage('kennel', owner(id))" :x="px(id) - 11" :y="py(id) - 32" width="22" height="20" class="piece-img" />

        <!-- псы (слева): одна фишка на владельца + счётчик -->
        <g v-for="(s, si) in dogOwners(id)" :key="'dog' + id + '-' + s">
          <image :href="pieceImage('dog', s)" :x="dogX(id, si)" :y="dogY(id, si)" :width="dogLayout.w" :height="dogLayout.h" class="piece-img" />
          <circle :cx="dogBadgeX(id, si)" :cy="dogBadgeY(id, si)" r="4.5" class="count-halo-white" />
          <text :x="dogBadgeX(id, si)" :y="dogBadgeY(id, si)" class="count-digit black" text-anchor="middle" dominant-baseline="central">{{ dogCountFor(id, s) }}</text>
        </g>

        <!-- шелудивые (справа): одна фишка + счётчик -->
        <g v-if="mangy(id) > 0">
          <image :href="pieceImage('mangy')" :x="px(id) + 17" :y="py(id) - 23" width="14" height="17" class="piece-img" />
          <circle :cx="px(id) + 22" :cy="py(id) - 15" r="4.7" class="count-halo-dark" />
          <text :x="px(id) + 22" :y="py(id) - 15" class="count-digit white" text-anchor="middle" dominant-baseline="central">{{ mangy(id) }}</text>
        </g>

        <!-- взрывчатка (между псами и шелудивыми) -->
        <image
          v-for="(b, i) in bombList(id)"
          :key="'x' + id + '-' + i"
          :href="bombImage(b.active && b.owner != null ? b.owner : null)"
          :x="px(id) - (bombList(id).length - 1) * 6 + i * 12 - 5"
          :y="py(id) - 11"
          width="10"
          height="10"
          class="piece-img"
        >
          <title>{{ bombInfo(b) }}</title>
        </image>

      </g>
      <!-- река и мосты (поверх гексов) -->
      <g v-for="(e, i) in riverEdges" :key="'b' + e.a + '-' + e.b">
        <image
          :href="riverAlt(e)"
          :x="midX(e) - riverLen / 2"
          :y="midY(e) - riverWidth / 2"
          :width="riverLen"
          :height="riverWidth"
          :transform="`rotate(${riverAngle(e)}, ${midX(e)}, ${midY(e)})`"
          preserveAspectRatio="xMidYMid meet"
          class="river-img"
        />
        <image
          :href="bridgeImage(isBroken(e.a, e.b))"
          :x="midX(e) - bridgeW / 2"
          :y="midY(e) - bridgeH / 2"
          :width="bridgeW"
          :height="bridgeH"
          :transform="`rotate(${bridgeAngle(e)}, ${midX(e)}, ${midY(e)})`"
          class="bridge-img"
        />
      </g>
      <!-- компромат и ресурсы (поверх реки) -->
      <g v-for="id in activeDistricts" :key="'top' + id">
        <image
          v-for="(seat, i) in kompromatList(id)"
          :key="'k' + id + '-' + i"
          :href="kompromatImage(seat)"
          :x="px(id) - (kompromatList(id).length - 1) * 6 + i * 12 - 8"
          :y="py(id) + 13"
          width="10"
          height="13"
          class="piece-img"
        />
        <g v-if="money(id)" :transform="`translate(${px(id) + 24}, ${py(id) + 15})`">
          <rect :x="-(moneyWidth(id) / 2)" y="-5" :width="moneyWidth(id)" height="10" rx="1.5" class="money-rect" />
          <text class="money-text" text-anchor="middle" dominant-baseline="central">{{ money(id) }}$</text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script>
import { HEX_COORDS, HEX_NUDGE, PLAYER_COLORS, hexToPixel, hexPoints } from '../board'
import { ABILITY_TITLES } from '../abilities'
import { districtImage, bridgeImage, riverAlt1Image, riverAlt2Image, pieceImage, kompromatImage, bombImage } from '../assets'

export default {
  name: 'Board',
  props: {
    state: { type: Object, required: true },
    districts: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      size: 42,        // радиус гекса (рендер)
      hexRotate: 30,   // поворот картинки района
      sqrt3: Math.sqrt(3),
      riverGap: 17,    // ширина реки (зазор между районами)
      riverLen: 52,    // длина сегмента реки вдоль русла 60
      riverWidth: 11.5,  // ширина сегмента реки поперёк русла 14
      bridgeW: 21,     // ширина моста (42 / 1.5)
      bridgeH: 12,     // высота моста (24 / 1.5)

      // === РАСКЛАДКА ПСОВ В РАЙОНЕ (правь значения, чтобы подогнать позиции) ===
      dogLayout: {
        baseX: -31,   // базовый сдвиг по X влево от центра района
        baseY: -25,   // базовый сдвиг по Y вверх от центра района
        stepX: -2,   // на сколько ВЛЕВО смещается пёс каждого следующего владельца
        stepY: 13,     // на сколько ВНИЗ смещается пёс каждого следующего владельца (высота пса 19 - 10 = 9)
        w: 16,        // ширина иконки пса
        h: 19,        // высота иконки пса
        badgeDX: 6,   // счётчик: вправо от левого края иконки
        badgeDY: 10   // счётчик: вниз от верхнего края иконки
      }
    }
  },
  computed: {
    activeDistricts() {
      return this.state.board_districts || []
    },
    riverEdges() {
      return (this.state.edges || []).filter((e) => e.kind === 'river')
    },
    hexOffsets() {
      const offs = {}
      const ids = this.activeDistricts
      for (const id of ids) offs[id] = { dx: 0, dy: 0 }

      // степень гекса по речным рёбрам
      const riverDegree = {}
      for (const e of this.riverEdges) {
        riverDegree[e.a] = (riverDegree[e.a] || 0) + 1
        riverDegree[e.b] = (riverDegree[e.b] || 0) + 1
      }

      // соседство по сухопутным рёбрам
      const landAdj = {}
      for (const e of (this.state.edges || [])) {
        if (e.kind !== 'land') continue
        ;(landAdj[e.a] = landAdj[e.a] || []).push(e.b)
        ;(landAdj[e.b] = landAdj[e.b] || []).push(e.a)
      }

      // «закреплённые» гексы: перекрёстки реки (степень >= 3) и их сухопутный кластер
      const pinned = {}
      const queue = []
      let anchor = null
      let maxDeg = 0
      for (const id of ids) {
        const d = riverDegree[id] || 0
        if (d >= 3) { pinned[id] = true; queue.push(id) }
        if (d > maxDeg) { maxDeg = d; anchor = id }
      }
      if (queue.length === 0 && anchor != null) { pinned[anchor] = true; queue.push(anchor) }
      while (queue.length) {
        const id = queue.pop()
        for (const nb of (landAdj[id] || [])) {
          if (!pinned[nb]) { pinned[nb] = true; queue.push(nb) }
        }
      }

      // раздвигаем только незакреплённые гексы от их речных соседей
      const push = this.riverGap / 2
      for (const e of this.riverEdges) {
        const aP = pinned[e.a], bP = pinned[e.b]
        const dx = this.basePx(e.b) - this.basePx(e.a)
        const dy = this.basePy(e.b) - this.basePy(e.a)
        const len = Math.hypot(dx, dy) || 1
        const ux = dx / len, uy = dy / len
        if (!aP) { offs[e.a].dx -= ux * push; offs[e.a].dy -= uy * push }
        if (!bP) { offs[e.b].dx += ux * push; offs[e.b].dy += uy * push }
      }
      return offs
    },
    riverAltMap() {
      const m = {}
      let u = 0, l = 0
      const pc = this.state.player_count
      // 3 игрока: нижняя (единственная) группа начинается с alt-1.
      // 4 игрока: обе группы перевёрнуты (alt-1 <-> alt-2).
      const lowerFirstAlt1 = pc === 3 || pc === 4
      const upperFirstAlt1 = pc !== 4
      for (const e of this.riverEdges) {
        const key = e.a + '-' + e.b
        if (this.midY(e) < 0) {
          m[key] = ((u % 2 === 0) === upperFirstAlt1) ? riverAlt1Image() : riverAlt2Image()
          u++
        } else {
          m[key] = ((l % 2 === 0) === lowerFirstAlt1) ? riverAlt1Image() : riverAlt2Image()
          l++
        }
      }
      return m
    },
    viewBox() {
      let minX = Infinity
      let minY = Infinity
      let maxX = -Infinity
      let maxY = -Infinity
      for (const id of this.activeDistricts) {
        const p = this.pos(id)
        minX = Math.min(minX, p.x)
        maxX = Math.max(maxX, p.x)
        minY = Math.min(minY, p.y)
        maxY = Math.max(maxY, p.y)
      }
      if (minX === Infinity) return '0 0 400 300'
      const pad = this.size * 1.4
      return `${minX - pad} ${minY - pad} ${maxX - minX + pad * 2} ${maxY - minY + pad * 2}`
    }
  },
  methods: {
    coord(id) {
      const c = HEX_COORDS[this.state.player_count] || {}
      return c[id] || [0, 0]
    },
    basePos(id) {
      const [q, r] = this.coord(id)
      return hexToPixel(q, r, this.size)
    },
    basePx(id) { return this.basePos(id).x },
    basePy(id) { return this.basePos(id).y },
    pos(id) {
      const base = this.basePos(id)
      const off = this.hexOffsets[id]
      const nudge = (HEX_NUDGE[this.state.player_count] || {})[id]
      let x = base.x + (off ? off.dx : 0)
      let y = base.y + (off ? off.dy : 0)
      if (nudge) { x += nudge.dx; y += nudge.dy }
      return { x, y }
    },
    px(id) { return this.pos(id).x },
    py(id) { return this.pos(id).y },
    hex(cx, cy) { return hexPoints(cx, cy, this.size) },
    d(id) { return this.state.districts[id] || {} },
    name(id) { return (this.districts[id] && this.districts[id].name) || String(id) },
    hasBuilding(id) {
      const o = this.d(id).building_owner
      return o !== null && o !== undefined
    },
    owner(id) {
      return this.d(id).building_owner
    },
    dogList(id) {
      const out = []
      const dogs = this.d(id).dogs || {}
      for (const seat of Object.keys(dogs)) {
        for (let i = 0; i < dogs[seat]; i++) out.push(Number(seat))
      }
      return out
    },
    allDogs(id) {
      const out = []
      for (const s of this.dogList(id)) out.push({ type: 'dog', seat: s })
      for (let i = 0; i < this.mangy(id); i++) out.push({ type: 'mangy', seat: null })
      return out
    },
    dogOwners(id) {
      const dogs = this.d(id).dogs || {}
      return Object.keys(dogs).filter((k) => (dogs[k] || 0) > 0).map(Number)
    },
    dogCountFor(id, seat) {
      return (this.d(id).dogs || {})[seat] || 0
    },
    dogX(id, si) { return this.px(id) + this.dogLayout.baseX + si * this.dogLayout.stepX },
    dogY(id, si) { return this.py(id) + this.dogLayout.baseY + si * this.dogLayout.stepY },
    dogBadgeX(id, si) { return this.dogX(id, si) + this.dogLayout.badgeDX },
    dogBadgeY(id, si) { return this.dogY(id, si) + this.dogLayout.badgeDY },
    mangy(id) { return this.d(id).mangy || 0 },
    money(id) { return this.d(id).money || 0 },
    moneyWidth(id) { return (String(this.money(id)) + '$').length * 3.4 + 2 },
    expl(id) { return (this.d(id).explosives || []).length },
    kompromatList(id) { return this.d(id).kompromat || [] },
    bombList(id) {
      return this.d(id).explosives || []
    },
    bombInfo(b) {
      if (!b.active) return 'Взрывчатка · неактивная'
      const owner = b.owner != null && b.owner !== undefined ? ('игрок ' + (b.owner + 1)) : 'без владельца'
      return 'Взрывчатка · ' + owner + ' · активная'
    },
    resSummary(id) {
      const parts = []
      if (this.mangy(id)) parts.push(`🐀${this.mangy(id)}`)
      if (this.money(id)) parts.push(`💰${this.money(id)}`)
      return parts.join(' ')
    },
    districtInfo(id) {
      const d = this.d(id)
      const parts = ['Район ' + id + ' · ' + this.name(id)]
      if (d.build_cost) parts.push('Постройка: ' + d.build_cost + '$')
      if (d.income) parts.push('Доход: ' + d.income + '$')
      const ab = d.ability
      if (ab) parts.push('Свойство: ' + (ABILITY_TITLES[ab.kind] || ab.kind || ''))
      return parts.join(' — ')
    },
    midX(e) { return (this.px(e.a) + this.px(e.b)) / 2 },
    midY(e) { return (this.py(e.a) + this.py(e.b)) / 2 },
    dx(e) { return this.px(e.b) - this.px(e.a) },
    dy(e) { return this.py(e.b) - this.py(e.a) },
    elen(e) { return Math.hypot(this.dx(e), this.dy(e)) || 1 },
    dirX(e) { return this.dx(e) / this.elen(e) },
    dirY(e) { return this.dy(e) / this.elen(e) },
    perpX(e) { return -this.dirY(e) },
    perpY(e) { return this.dirX(e) },
    isBroken(a, b) {
      const key = [Math.min(a, b), Math.max(a, b)]
      return (this.state.broken_bridges || []).some((k) => k[0] === key[0] && k[1] === key[1])
    },
    color(seat) { return PLAYER_COLORS[seat] || '#999' },
    districtImage,
    bridgeImage,
    pieceImage,
    kompromatImage,
    bombImage,
    baseDx(e) { return this.basePx(e.b) - this.basePx(e.a) },
    baseDy(e) { return this.basePy(e.b) - this.basePy(e.a) },
    bridgeAngle(e) { return Math.atan2(this.baseDy(e), this.baseDx(e)) * 180 / Math.PI },
    riverAngle(e) {
      // perp = (-baseDy, baseDx); картинка реки горизонтальна (0°)
      return Math.atan2(this.baseDx(e), -this.baseDy(e)) * 180 / Math.PI
    },
    riverAlt(e) { return this.riverAltMap[e.a + '-' + e.b] }
  }
}
</script>

<style scoped>
.board-wrap { overflow-x: auto; }
.board { display: block; max-width: 100%; min-width: 460px; margin: 0 auto; }
.hex { fill: url(#hex-grad); stroke: #c4bdae; stroke-width: 1.5; }
.river { stroke: #7fb5d9; stroke-width: 9; stroke-linecap: round; opacity: 0.55; }
.bridge { stroke: #7a5c3e; stroke-width: 5; stroke-linecap: round; }
.bridge.broken { stroke: #c33; stroke-dasharray: 8 6; }
.dname { font-size: 11px; fill: #666; text-anchor: middle; }
.dimg { pointer-events: none; }
.bridge-img { filter: drop-shadow(0 1px 1px rgba(0,0,0,0.35)); }
.river-img { pointer-events: none; }
.piece-img { pointer-events: none; animation: pop 0.28s cubic-bezier(0.2, 0.8, 0.3, 1); }
.count-halo-white { fill: #ffffff00; }
.count-halo-dark { fill: rgba(0, 0, 0, 0); }
.count-digit { font-size: 8px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }
.count-digit.black { fill: #111; }
.count-digit.white { fill: #fff; font-size: 7.3px; }
.bld { font-size: 16px; text-anchor: middle; }
.bldnum { text-anchor: middle; dominant-baseline: central; fill: #fff; font-size: 12px; font-weight: 700; }
.money-rect { fill: #e3f0dc; stroke: #b7dc00; stroke-width: 1; filter: drop-shadow(0 1px 1.5px rgba(0,0,0,0.25))}
.money-text { fill: #245a22; font-size: 6px; font-weight: 600; text-anchor: middle; letter-spacing: -0.2px; }
.mangy-text { fill: #555; font-size: 10px; }
.komp { font-size: 12px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }
.bombx { fill: #fff; font-size: 9px; font-weight: 900; text-anchor: middle; dominant-baseline: central; pointer-events: none; }
</style>