<template>
  <div class="starry-bg">
    <div class="stars">
      <div v-for="star in stars" :key="star.id" class="star" :style="star.style"></div>
    </div>
    <div class="lines">
      <div v-for="line in lines" :key="line.id" class="line" :style="line.style"></div>
    </div>
    <div class="gradient-overlay"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stars = ref([])
const lines = ref([])

function generateStars() {
  const starList = []
  for (let i = 0; i < 150; i++) {
    const size = Math.random() * 3 + 1
    starList.push({
      id: i,
      style: {
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        width: `${size}px`,
        height: `${size}px`,
        animationDelay: `${Math.random() * 5}s`,
        animationDuration: `${Math.random() * 3 + 2}s`
      }
    })
  }
  stars.value = starList
}

function generateLines() {
  const lineList = []
  for (let i = 0; i < 30; i++) {
    lineList.push({
      id: i,
      style: {
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        width: `${Math.random() * 200 + 50}px`,
        transform: `rotate(${Math.random() * 360}deg)`,
        opacity: Math.random() * 0.3 + 0.1
      }
    })
  }
  lines.value = lineList
}

onMounted(() => {
  generateStars()
  generateLines()
})
</script>

<style scoped>
.starry-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(ellipse at center, #1a1a2e 0%, #0d0d1a 50%, #000000 100%);
  overflow: hidden;
  z-index: -1;
}

.stars {
  position: absolute;
  width: 100%;
  height: 100%;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle ease-in-out infinite;
  box-shadow: 0 0 6px 1px rgba(100, 200, 255, 0.3);
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.lines {
  position: absolute;
  width: 100%;
  height: 100%;
}

.line {
  position: absolute;
  height: 1px;
  background: linear-gradient(90deg, rgba(100, 180, 255, 0) 0%, rgba(100, 180, 255, 0.4) 50%, rgba(100, 180, 255, 0) 100%);
}

.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(ellipse at 30% 50%, rgba(64, 158, 255, 0.15) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 30%, rgba(118, 75, 162, 0.1) 0%, transparent 40%),
              radial-gradient(ellipse at 50% 80%, rgba(0, 200, 255, 0.08) 0%, transparent 30%);
}
</style>