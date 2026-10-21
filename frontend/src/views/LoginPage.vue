<script setup>
import { onMounted, ref } from 'vue'
import { beginKakaoLogin, completeKakaoCallback, postLogin, redirectToMain } from '../api/kakaoAuth.mjs'
import { CourseAuthDialog, CoursePageLayout } from '../components/index.js'

const mode = ref('login')
const loading = ref(false)
const message = ref('')
const success = ref(false)
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const kakaoRedirectUri = window.location.origin + '/login/kakao/callback'

async function finishKakaoCallback() {
  if (window.location.pathname !== '/login/kakao/callback') return
  loading.value = true
  const result = await completeKakaoCallback({
    search: window.location.search,
    storage: window.sessionStorage,
    history: window.history,
    exchangeCode: (code) => postLogin({ apiBaseUrl, path: '/user/kakao/login', payload: { code } }),
  })
  if (result.ok) redirectToMain()
  else message.value = ({
    invalid_state: '로그인 요청을 확인할 수 없습니다. 다시 시도해 주세요.',
    cancelled: '카카오 로그인을 취소했습니다.',
    missing_code: '인증 정보를 받지 못했습니다. 다시 시도해 주세요.',
    exchange_failed: '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.',
  })[result.error] || '카카오 로그인 중 문제가 생겼습니다.'
  loading.value = false
}

onMounted(finishKakaoCallback)

async function submit(credentials) {
  mode.value = credentials.mode
  message.value = ''
  success.value = false
  loading.value = true
  try {
    const response = await fetch(apiBaseUrl + '/user/' + credentials.mode, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials.mode === 'signup'
        ? { name: credentials.name, email: credentials.email, password: credentials.password }
        : { email: credentials.email, password: credentials.password }),
    })
    const body = await response.json()
    if (!response.ok) {
      if (response.status === 409) throw new Error('이미 가입된 이메일입니다. 로그인해 주세요.')
      if (response.status === 401) throw new Error('이메일 또는 비밀번호를 확인해 주세요.')
      if (response.status === 422) throw new Error('입력 정보를 다시 확인해 주세요.')
      throw new Error(typeof body.result === 'string' ? body.result : '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.')
    }
    if (credentials.mode === 'signup') {
      mode.value = 'login'
      success.value = true
      message.value = '가입이 완료되었습니다. 로그인해 주세요.'
    } else redirectToMain()
  } catch (reason) {
    message.value = reason instanceof TypeError
      ? '서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.'
      : reason.message
  } finally { loading.value = false }
}

function startKakaoLogin() {
  message.value = ''
  try {
    const bytes = new Uint8Array(16)
    window.crypto.getRandomValues(bytes)
    const state = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
    beginKakaoLogin({ sdk: window.Kakao, key: import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY, redirectUri: kakaoRedirectUri, storage: window.sessionStorage, state })
  } catch { message.value = '카카오 로그인을 준비하지 못했습니다. 설정을 확인해 주세요.' }
}

function closeDialog() { window.location.assign('/') }
</script>

<template>
  <CoursePageLayout active-page="auth">
    <section class="login-welcome">
      <span>MOA LEARNING</span><h1>작은 배움이<br /><em>큰 변화를 만듭니다.</em></h1><p>관심 있는 분야를 배우고, 내일의 가능성을 넓혀보세요.</p>
      <div class="login-welcome__art" aria-hidden="true"><span>Learn<br />what's next</span><i></i><b></b></div>
    </section>
    <CourseAuthDialog :model-value="true" :initial-mode="mode" :loading="loading" :error="success ? '' : message" :notice="success ? message : ''" @submit="submit" @social-login="startKakaoLogin" @switch-mode="mode = $event" @update:model-value="closeDialog" />
  </CoursePageLayout>
</template>

<style scoped>
.login-welcome { position: relative; min-height: 360px; display: flex; flex-direction: column; justify-content: center; padding: 55px clamp(18px, 6vw, 70px); overflow: hidden; }
.login-welcome > span { color: #6d3ca8; font-size: 10px; font-weight: 800; letter-spacing: 1.6px; }
.login-welcome h1 { position: relative; z-index: 1; margin: 15px 0 10px; color: #30253c; font-size: clamp(36px, 5vw, 58px); font-weight: 650; letter-spacing: -2px; line-height: 1.2; }
.login-welcome h1 em { color: #5d1eb7; font-style: normal; }
.login-welcome p { position: relative; z-index: 1; margin: 0; color: #6f6679; font-size: 13px; }
.login-welcome__art { position: absolute; top: 34px; right: 8%; display: grid; place-items: center; width: 220px; height: 220px; border-radius: 45% 55% 55% 45%; background: #e7dcf4; color: #613b91; transform: rotate(-12deg); }
.login-welcome__art span { z-index: 1; font-size: 21px; font-weight: 800; letter-spacing: -1px; line-height: 1.08; text-align: center; transform: rotate(12deg); }
.login-welcome__art i, .login-welcome__art b { position: absolute; inset: 18px 34px; border: 1px solid #ab8dd0; border-radius: 50%; }.login-welcome__art b { inset: 32px 10px; transform: rotate(55deg); }
@media (max-width: 620px) { .login-welcome { min-height: 275px; justify-content: flex-start; padding: 44px 7px 20px; }.login-welcome__art { top: 75px; right: -90px; opacity: .55; }.login-welcome h1 { font-size: 37px; } }
</style>
