<script setup>
import { onMounted, ref } from 'vue'
import { fetchCurrentUser } from '../api/kakaoAuth.mjs'

defineProps({ activePage: { type: String, default: 'catalog' } })

const profile = ref(null)
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

onMounted(async () => {
  try {
    profile.value = await fetchCurrentUser({ apiBaseUrl })
  } catch {
    profile.value = null
  }
})
</script>

<template>
  <div class="academy-shell">
    <header class="academy-header">
      <a class="academy-brand" href="/" aria-label="모아 아카데미 홈">
        <span class="academy-brand__mark" aria-hidden="true">M</span><span>MOA <b>Academy</b></span>
      </a>
      <nav class="academy-nav" aria-label="주요 메뉴">
        <a href="/courses" :aria-current="activePage === 'catalog' ? 'page' : undefined">강의 찾기</a>
        <a href="/courses" :aria-current="activePage === 'detail' ? 'page' : undefined">내 학습</a>
      </nav>
      <a v-if="!profile" class="academy-account" href="/login">로그인 <span aria-hidden="true">↗</span></a>
      <div v-else class="academy-profile">
        <span class="academy-profile__avatar" role="img" :aria-label="`${profile.name} 프로필`">
          {{ profile.name?.trim()?.slice(0, 1) || 'M' }}
        </span>
        <span class="academy-profile__name">{{ profile.name }}</span>
      </div>
    </header>
    <main class="academy-main"><slot /></main>
    <footer class="academy-footer"><a href="/">MOA Academy</a><span>배움으로 다음 가능성을 만듭니다</span><span>© {{ new Date().getFullYear() }} MOA Academy</span></footer>
  </div>
</template>

<style scoped>
.academy-shell { --academy-brand: var(--brand, #5d1eb7); min-height: 100vh; display: flex; flex-direction: column; background: #fbfaff; color: #292331; }
.academy-header { position: sticky; z-index: 20; top: 0; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; min-height: 76px; padding: 0 max(5vw, calc((100vw - 1180px) / 2)); border-bottom: 1px solid #ece8f1; background: #ffffffed; backdrop-filter: blur(12px); }
.academy-brand { display: inline-flex; align-items: center; gap: 10px; width: fit-content; color: #292331; font-size: 15px; font-weight: 800; letter-spacing: -.5px; text-decoration: none; }
.academy-brand b { color: var(--academy-brand); }
.academy-brand__mark { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 11px 11px 11px 3px; background: var(--academy-brand); color: #fff; font-size: 17px; }
.academy-nav { display: flex; align-items: center; gap: 28px; height: 100%; }
.academy-nav a { display: grid; align-items: center; height: 100%; border-bottom: 2px solid transparent; color: #6b6472; font-size: 12px; text-decoration: none; }
.academy-nav a[aria-current="page"] { border-color: var(--academy-brand); color: var(--academy-brand); font-weight: 700; }
.academy-account { justify-self: end; padding: 10px 14px; border: 1px solid #e4dfeb; border-radius: 999px; color: #423a49; font-size: 12px; font-weight: 650; text-decoration: none; }
.academy-account:hover { border-color: var(--academy-brand); color: var(--academy-brand); }
.academy-account span { padding-left: 8px; color: var(--academy-brand); }
.academy-profile { justify-self: end; display: flex; align-items: center; gap: 9px; min-width: 0; color: #423a49; font-size: 12px; font-weight: 650; }
.academy-profile__avatar { display: grid; place-items: center; width: 36px; height: 36px; flex: 0 0 36px; border: 2px solid #e8ddf5; border-radius: 50%; background: #f1eafa; color: var(--academy-brand); font-size: 14px; font-weight: 750; }
.academy-profile__name { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.academy-main { width: min(1180px, calc(100% - 48px)); flex: 1; margin: 0 auto; }
.academy-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 65px; margin-top: 50px; padding: 10px max(5vw, calc((100vw - 1180px) / 2)); border-top: 1px solid #ece8f1; color: #817987; font-size: 11px; }
.academy-footer a { color: var(--academy-brand); font-weight: 750; text-decoration: none; }
.academy-header a:focus-visible, .academy-footer a:focus-visible { outline: 3px solid #c9b4e8; outline-offset: 3px; border-radius: 5px; }
@media (max-width: 640px) { .academy-header { grid-template-columns: 1fr auto; min-height: 66px; padding: 0 18px; } .academy-brand { font-size: 13px; } .academy-brand__mark { width: 31px; height: 31px; } .academy-nav { display: none; } .academy-profile__name { display: none; } .academy-main { width: min(100% - 32px, 1180px); } .academy-footer { align-items: flex-start; flex-direction: column; gap: 5px; padding: 18px; } }
</style>
