<!-- views/SecurityAuditContact.vue -->
<template>
  <div class="security-audit-layout">
    <!-- 모바일 메뉴 토글 버튼 -->
    <button
      v-if="sidebarRef?.isMobile"
      @click="sidebarRef?.toggleSidebar()"
      class="mobile-menu-toggle"
    >
      <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
        <path
          fill-rule="evenodd"
          d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"
        />
      </svg>
    </button>

    <main class="dashboard-page">
      <div class="page-header">
        <h1 class="page-title">문의사항</h1>
      </div>

      <!-- 개요 섹션 -->
      <div class="section">
        <h2 class="section-title">보안 감사 관련 문의</h2>
        <p>
          정보보안 감사 시스템 사용 중 궁금한 사항이나 기술적 문제가 있으시면 언제든지 운영실로
          연락 주시기 바랍니다. 신속하고 정확한 답변을 드리도록 하겠습니다.
        </p>
      </div>

      <!-- 연락처 정보 -->
      <div class="section">
        <h2 class="section-title">연락처 정보</h2>
        <div class="contact-grid">
          <!-- 첫 번째 담당자 -->
          <div class="contact-card">
            <div class="contact-icon phone">
              <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
              </svg>
            </div>
            <div class="contact-content">
              <h3>OOO</h3>
              <p class="contact-detail">내선 <strong>1111</strong></p>
              <p class="contact-description">평일 09:00 - 18:00</p>
              <button @click="copyToClipboard('5678')" class="copy-button small">
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                  <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                </svg>
                복사
              </button>
            </div>
          </div>

          <!-- 두 번째 담당자 -->
          <div class="contact-card">
            <div class="contact-icon phone">
              <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
              </svg>
            </div>
            <div class="contact-content">
              <h3>OOO</h3>
              <p class="contact-detail">내선 <strong>1111</strong></p>
              <p class="contact-description">평일 09:00 - 18:00</p>
              <button @click="copyToClipboard('5678')" class="copy-button small">
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                  <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                </svg>
                복사
              </button>
            </div>
          </div>

          <!-- 세 번째 담당자 -->
          <div class="contact-card">
            <div class="contact-icon phone">
              <svg width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
              </svg>
            </div>
            <div class="contact-content">
              <h3>OOO</h3>
              <p class="contact-detail">내선 <strong>1111</strong></p>
              <p class="contact-description">평일 09:00 - 18:00</p>
              <button @click="copyToClipboard('5678')" class="copy-button small">
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                  <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                </svg>
                복사
              </button>
            </div>
          </div>
        </div>
      </div>
      <!-- 자주 묻는 질문 -->
      <!-- <div class="section">
        <h2 class="section-title">자주 묻는 질문</h2>
        <div class="faq-container">
          <div v-for="(faq, index) in faqList" :key="index" class="faq-item">
            <button
              @click="toggleFaq(index)"
              :class="['faq-question', { active: activeFaq === index }]"
            >
              <span class="faq-question-text">{{ faq.question }}</span>
              <span class="faq-toggle-icon">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path
                    fill-rule="evenodd"
                    d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"
                  />
                </svg>
              </span>
            </button>
            <Transition name="faq">
              <div v-if="activeFaq === index" class="faq-answer">
                <div class="faq-answer-content">
                  <p v-html="faq.answer"></p>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div> -->

      <!-- 문의 양식 -->

      <!-- 토스트 메시지 -->
      <div v-if="showToast" :class="['toast-message', toastType]">
        {{ toastMessage }}
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute } from 'vue-router'

// Vue Router
const route = useRoute()

// 반응형 데이터
const activeFaq = ref(null)
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
const isSubmitting = ref(false)
// Sidebar ref 추가
const sidebarRef = ref(null)

// 폼 데이터
const form = reactive({
  name: '',
  department: '',
  email: '',
  phone: '',
  category: '',
  subject: '',
  message: '',
  agreePrivacy: false,
})

// FAQ 데이터
const faqList = [
  {
    question: '보안 감사는 얼마나 자주 실시되나요?',
    answer:
      '정기 보안 감사는 매일 실시되며, 필요에 따라 수시 감사도 진행됩니다. 시스템을 통해 언제든지 현재 상태를 확인하실 수 있습니다.',
  },
  {
    question: '감사 결과에서 실패 항목이 있을 때 어떻게 해야 하나요?',
    answer:
      '<strong>조치방법</strong> 페이지에서 각 항목별 상세한 해결 방법을 확인하실 수 있습니다. 기술적 도움이 필요한 경우 운영실로 연락주시기 바랍니다.',
  },
  {
    question: '시스템 접속에 문제가 있어요.',
    answer:
      '로그인 문제의 경우 먼저 브라우저 캐시를 삭제하고 다시 시도해 보세요. 문제가 지속되면 운영실로 연락 주시기 바랍니다.',
  },
  {
    question: '개인 PC에서도 보안 감사를 받아야 하나요?',
    answer:
      '회사 네트워크에 연결된 모든 PC는 보안 정책 준수 대상입니다. 개인 소유 장비라도 업무용으로 사용하는 경우 보안 감사 대상에 포함됩니다.',
  },
]

// 메서드
const toggleFaq = (index) => {
  activeFaq.value = activeFaq.value === index ? null : index
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    showToastMessage('클립보드에 복사되었습니다!', 'success')
  } catch (err) {
    console.error('클립보드 복사 실패:', err)
    fallbackCopyTextToClipboard(text)
  }
}

const fallbackCopyTextToClipboard = (text) => {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.top = '0'
  textArea.style.left = '0'
  textArea.style.position = 'fixed'

  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()

  try {
    const successful = document.execCommand('copy')
    if (successful) {
      showToastMessage('클립보드에 복사되었습니다!', 'success')
    }
  } catch (err) {
    console.error('Fallback: 클립보드 복사 실패', err)
    showToastMessage('복사에 실패했습니다.', 'error')
  }

  document.body.removeChild(textArea)
}

const showToastMessage = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true

  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

const submitForm = async () => {
  isSubmitting.value = true

  try {
    // 실제 API 호출 시뮬레이션
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // TODO: 실제 API 호출
    console.log('문의 양식 제출:', form)

    showToastMessage('문의가 성공적으로 접수되었습니다!', 'success')
    resetForm()
  } catch (error) {
    console.error('문의 제출 실패:', error)
    showToastMessage('문의 제출 중 오류가 발생했습니다.', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  Object.keys(form).forEach((key) => {
    if (typeof form[key] === 'boolean') {
      form[key] = false
    } else {
      form[key] = ''
    }
  })
}

const showPrivacyPolicy = () => {
  alert('개인정보 수집 및 이용 방침에 대한 상세 내용을 별도 창에서 확인하실 수 있습니다.')
}
</script>

<!-- CSS는 외부 파일에서 import -->
<style scoped>
@import '../styles/ContactPage.css';
</style>