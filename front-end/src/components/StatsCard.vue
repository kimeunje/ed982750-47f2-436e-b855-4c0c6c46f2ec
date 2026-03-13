<template>
  <div class="stats-card">
    <h3 class="stats-title">{{ title }}</h3>
    <p class="stats-value" :class="getColorClass">
      {{ value }}
    </p>
    <p class="stats-subtitle">{{ subtitle }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  valueColor: {
    type: String,
    default: '',
  },
})

const getColorClass = computed(() => {
  switch (props.valueColor) {
    case 'green':
      return 'color-green'
    case 'red':
      return 'color-red'
    case 'blue':
      return 'color-blue'
    default:
      return 'color-default'
  }
})
</script>
<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import './styles/StatsCard.css';
</style>
