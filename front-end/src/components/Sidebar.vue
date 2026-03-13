<!-- src/components/Sidebar.vue -->
<!-- Sidebar.vue 템플릿을 다음과 같이 수정 -->
<template>
  <!-- 데스크톱에서는 항상 표시, 모바일에서는 조건부 표시 -->
  <aside v-show="!isMobile || isOpen" :class="['sidebar', { 'mobile-open': isMobile && isOpen }]">
    <div class="sidebar-title">정보보안 감사 현황</div>
    <ul class="sidebar-menu">
      <li v-for="mainItem in MENU_STRUCTURE" :key="mainItem.id" class="sidebar-main-item">
        <RouterLink
          :to="mainItem.path"
          :class="{ active: isParentPath(mainItem.path) }"
          @click="isMobile && closeSidebar()"
        >
          {{ mainItem.title }}
        </RouterLink>

        <!-- 하위 메뉴가 있고, 현재 항목이 활성화되어 있으면 하위 메뉴 표시 -->
        <ul
          v-if="mainItem.subItems.length > 0 && isParentPath(mainItem.path)"
          class="sidebar-submenu"
        >
          <li v-for="subItem in mainItem.subItems" :key="subItem.id">
            <RouterLink
              :to="subItem.path"
              :class="{ active: isPathActive(subItem.path) }"
              @click="isMobile && closeSidebar()"
            >
              {{ subItem.title }}
            </RouterLink>
          </li>
        </ul>
      </li>
    </ul>
  </aside>

  <!-- 모바일 오버레이 -->
  <div v-if="isMobile && isOpen" class="sidebar-overlay" @click="closeSidebar"></div>
</template>

<script setup>
// src/components/Sidebar.vue의 <script setup> 부분에 추가

import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { MENU_STRUCTURE } from '@/data/security-audit-config'

// Vue Router
const route = useRoute()

// 반응형 데이터 추가
const isMobile = ref(false)
const isOpen = ref(false)

// 기존 메서드들...
const isPathActive = (path) => {
  return route.path === path
}

const isParentPath = (path) => {
  if (route.path === path) return true
  return route.path.startsWith(`${path}/`)
}

// 새로 추가할 메서드들
const checkScreenSize = () => {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) {
    isOpen.value = false
  }
}

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
}

const closeSidebar = () => {
  isOpen.value = false
}

// 라이프사이클 훅
onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})

// 외부에서 사용할 수 있도록 expose
defineExpose({
  toggleSidebar,
  isOpen,
  isMobile,
})
</script>

<!-- CSS는 외부 파일에서 import -->
<style>
@import './styles/Sidebar.css';
</style>
