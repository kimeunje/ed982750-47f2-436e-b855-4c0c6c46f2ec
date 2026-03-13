<!-- components/PageNavigation.vue -->
<template>
  <div class="pagination">
    <button @click="goToPrevious" :disabled="!prevItem" :class="{ disabled: !prevItem }">
      {{ prevItem ? `이전: ${prevItem.title}` : '이전' }}
    </button>

    <button @click="goToNext" :disabled="!nextItem" :class="{ disabled: !nextItem }">
      {{ nextItem ? `다음: ${nextItem.title}` : '다음' }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getPreviousMenuItem, getNextMenuItem } from '@/data/security-audit-config'

// Props 정의
const props = defineProps({
  currentPath: {
    type: String,
    required: true,
  },
})

// Vue Router
const router = useRouter()

// 계산된 속성
const prevItem = computed(() => getPreviousMenuItem(props.currentPath))
const nextItem = computed(() => getNextMenuItem(props.currentPath))

// 메서드
const goToPrevious = () => {
  if (prevItem.value) {
    router.push(prevItem.value.path)
  }
}

const goToNext = () => {
  if (nextItem.value) {
    router.push(nextItem.value.path)
  }
}
</script>

<!-- CSS는 외부 파일에서 import -->
<style>
@import './styles/PageNavigation.css';
</style>
