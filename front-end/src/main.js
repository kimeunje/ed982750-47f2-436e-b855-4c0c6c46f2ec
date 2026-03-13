// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 에러 핸들링
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue 에러:', err)
  console.error('컴포넌트:', vm)
  console.error('정보:', info)
}

// 개발 모드 설정
if (import.meta.env.DEV) {
  app.config.devtools = true

  // 개발 모드에서만 성능 추적 활성화
  app.config.performance = true

  console.log('🚀 개발 모드로 애플리케이션이 시작되었습니다.')
  console.log('📊 Vue DevTools가 활성화되었습니다.')
}

app.mount('#app')

// 개발 환경에서 앱 인스턴스를 전역으로 노출 (디버깅용)
if (import.meta.env.DEV) {
  window.__VUE_APP__ = app
}
