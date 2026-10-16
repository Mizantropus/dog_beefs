<template>
  <div class="dice-scene" :style="{ width: size + 'px', height: size + 'px' }">
    <div class="dice-shadow" :style="{ width: Math.round(size * 0.9) + 'px' }"></div>
    <div class="dice-cube" :style="cubeStyle">
      <div v-for="(f, i) in faceOrder" :key="i" class="dice-face" :style="faceStyle(i)">
        <img :src="faceImage(f)" :alt="'Грань ' + (f + 1)" />
      </div>
    </div>
  </div>
</template>

<script>
import { dieFaceImage } from '../assets'

// Порядок граней куба: [передняя, задняя, правая, левая, верхняя, нижняя].
// Противоположные грани совпадают с OPPOSITE_FACE бэкенда: 0-5, 1-4, 2-3.
const FACE_ORDER = [0, 5, 1, 4, 2, 3]

const FACE_ROT = [
  'rotateY(0deg)',    // передняя
  'rotateY(180deg)',  // задняя
  'rotateY(90deg)',   // правая
  'rotateY(-90deg)',  // левая
  'rotateX(90deg)',   // верхняя
  'rotateX(-90deg)'   // нижняя
]

// Куда повернуть куб, чтобы грань face смотрела на зрителя (передняя = +z).
const SETTLE = {
  0: { x: 0, y: 0 },      // передняя
  1: { x: 0, y: -90 },    // правая
  2: { x: -90, y: 0 },    // верхняя
  3: { x: 90, y: 0 },     // нижняя
  4: { x: 0, y: 90 },     // левая
  5: { x: 0, y: 180 }     // задняя
}

export default {
  name: 'DiceCube',
  props: {
    face: { type: Number, default: 0 },
    size: { type: Number, default: 64 },
    faces: { type: Array, default: null }
  },
  data() {
    return {
      rotX: 0,
      rotY: 0,
      faceOrder: FACE_ORDER
    }
  },
  computed: {
    cubeStyle() {
      return { transform: 'rotateX(' + this.rotX + 'deg) rotateY(' + this.rotY + 'deg)' }
    }
  },
  mounted() {
    // при появлении показываем бросок кубика
    setTimeout(() => this.roll(), 30)
  },
  watch: {
    face() { this.roll() }
  },
  methods: {
    dieFaceImage,
    faceImage(f) {
      if (this.faces && this.faces.length === 6) return this.faces[f]
      return dieFaceImage(f)
    },
    faceStyle(i) {
      return { transform: FACE_ROT[i] + ' translateZ(' + (this.size / 2) + 'px)' }
    },
    roll() {
      const s = SETTLE[this.face] || SETTLE[0]
      const rx = (2 + Math.floor(Math.random() * 3)) * 360
      const ry = (3 + Math.floor(Math.random() * 3)) * 360
      this.rotX = s.x + rx
      this.rotY = s.y + ry
    }
  }
}
</script>

<style scoped>
.dice-scene { position: relative; margin-right: 10px; display: inline-block; vertical-align: middle; perspective: 520px; }
.dice-shadow {
  position: absolute;
  left: 50%;
  bottom: -7px;
  transform: translateX(-50%);
  height: 8px;
  background: rgba(0, 0, 0, 0.18);
  border-radius: 50%;
  filter: blur(2px);
}
.dice-cube {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 1.4s cubic-bezier(0.2, 0.8, 0.25, 1);
}
.dice-face {
  position: absolute;
  width: 100%;
  height: 100%;
  background: #fff;
  border: 1px solid #d8d2c4;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  backface-visibility: hidden;
  box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.06);
}
.dice-face img { width: 76%; height: 76%; object-fit: contain; }
</style>
