// stores/auth.js - IP 인증으로 수정
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 상태 (State)
  const user = ref(null)
  const loading = ref(true)
  const authError = ref(null)

  // 계산된 속성 (Getters)
  const isAuthenticated = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || '')
  const userRole = computed(() => user.value?.role || 'user')

  // 액션 (Actions)

  // 초기 로드시 사용자 정보 가져오기 (기존 유지)
  const loadUserInfo = async () => {
    loading.value = true
    try {
      console.log('사용자 인증 상태 확인 중...')

      const response = await fetch('/api/auth/me', {
        credentials: 'include', // 쿠키 포함
      })

      console.log('인증 응답 상태:', response.status)

      if (response.ok) {
        const userData = await response.json()

        if (userData.authenticated) {
          console.log('인증 성공:', userData)
          user.value = userData
          authError.value = null
        } else {
          console.log('인증 실패: 토큰은 있지만 유효하지 않음')
          user.value = null
          authError.value = '인증 세션이 만료되었습니다'
          // 쿠키가 있지만 유효하지 않은 경우, 쿠키 삭제
          await logout(false) // 리디렉션 없이 로그아웃
        }
      } else {
        console.log('인증 요청 실패:', response.status)
        user.value = null
        const errorData = await response.json().catch(() => ({}))
        authError.value = errorData.message || '인증에 실패했습니다'

        if (response.status === 401) {
          // 토큰이 만료된 경우 쿠키 삭제
          document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
        }
      }
    } catch (error) {
      console.error('인증 상태 확인 중 오류 발생:', error)
      user.value = null
      authError.value = '인증 확인 중 오류가 발생했습니다'
    } finally {
      loading.value = false
    }
  }

  // IP 기반 인증 확인 (LDAP 대체)
  const checkIpAuthentication = async () => {
    try {
      console.log('IP 인증 요청 시작...')

      const response = await fetch('/api/auth/check-ip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })

      const result = await response.json()

      if (!response.ok) {
        console.error('IP 인증 실패:', response.status, result)
        throw new Error(result.message || 'IP 인증에 실패했습니다.')
      }

      console.log('IP 인증 성공:', result)
      return result
    } catch (error) {
      console.error('IP 인증 오류:', error)
      return { success: false, error: error.message }
    }
  }

  // 이메일 인증 코드 요청 (기존 유지)
  const requestVerificationCode = async (email) => {
    try {
      const response = await fetch('/api/auth/email-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
        credentials: 'include',
      })

      return await response.json()
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  // 인증 코드 확인 및 최종 로그인 (IP 기반으로 수정)
  const verifyAndLogin = async (email, code, username) => {
    try {
      console.log('최종 로그인 시도:', { email, username })

      const response = await fetch('/api/auth/verify-and-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, code, username }),
        credentials: 'include',
      })

      if (!response.ok) {
        const error = await response.json()
        console.error('로그인 실패:', response.status, error)
        throw new Error(error.message || '인증에 실패했습니다.')
      }

      console.log('로그인 성공, 사용자 정보 조회 중...')

      // 사용자 정보 가져오기
      const userResponse = await fetch('/api/auth/me', {
        credentials: 'include',
      })

      if (userResponse.ok) {
        const userData = await userResponse.json()
        if (userData.authenticated) {
          user.value = userData
          authError.value = null
          console.log('사용자 정보 설정 완료:', userData)
          return { success: true }
        } else {
          throw new Error('사용자 정보 인증에 실패했습니다.')
        }
      } else {
        throw new Error('사용자 정보를 가져오는데 실패했습니다.')
      }
    } catch (error) {
      console.error('verifyAndLogin 오류:', error)
      return { success: false, error: error.message }
    }
  }

  // 로그아웃 (기존 유지)
  const logout = async (redirect = true) => {
    try {
      // 서버에 로그아웃 요청
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })

      user.value = null
      authError.value = null

      console.log('로그아웃 완료')

      // 리디렉션 옵션이 true인 경우만 로그인 페이지로 이동
      if (redirect) {
        window.location.href = '/login'
      }
    } catch (error) {
      console.error('로그아웃 중 오류 발생:', error)
    }
  }

  // 인증 상태 새로고침 (기존 유지)
  const refreshAuthState = async () => {
    loading.value = true

    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      })

      if (response.ok) {
        const userData = await response.json()
        if (userData.authenticated) {
          user.value = userData
          authError.value = null
        } else {
          user.value = null
          authError.value = '인증 세션이 만료되었습니다'
          await logout(false)
        }
      } else {
        user.value = null
        authError.value = '인증에 실패했습니다'
      }
    } catch (error) {
      console.error('인증 상태 새로고침 중 오류:', error)
      user.value = null
      authError.value = '인증 확인 중 오류가 발생했습니다'
    } finally {
      loading.value = false
    }
  }

  // 초기화 시 사용자 정보 로드 (기존 유지)
  const initialize = async () => {
    await loadUserInfo()
  }

  // 현재 IP 정보 조회 (디버깅용)
  const getCurrentIpInfo = async () => {
    try {
      const response = await fetch('/api/auth/ip-info', {
        credentials: 'include',
      })

      if (response.ok) {
        return await response.json()
      } else {
        throw new Error('IP 정보 조회 실패')
      }
    } catch (error) {
      console.error('IP 정보 조회 오류:', error)
      return { error: error.message }
    }
  }

  return {
    // 상태
    user,
    loading,
    authError,

    // 계산된 속성
    isAuthenticated,
    userName,
    userRole,

    // 액션
    initialize,
    loadUserInfo,
    checkIpAuthentication, // 새로운 IP 인증 메서드
    requestVerificationCode,
    verifyAndLogin,
    logout,
    refreshAuthState,
    getCurrentIpInfo, // IP 정보 조회 메서드
  }
})
