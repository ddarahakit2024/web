<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCurrentUser } from '../api/kakaoAuth.mjs'
import { filterPosts } from '../stores/postFilters.js'

const categories = [
  { name: '추천', icon: '✦' },
  { name: '바다', icon: '⌁' },
  { name: '자연 속으로', icon: '♧' },
  { name: '도시 산책', icon: '⌂' },
  { name: '혼자 여행', icon: '◌' },
  { name: '맛집 탐방', icon: '♨' },
  { name: '주말 여행', icon: '☼' },
]

const posts = ref([
  {
    id: 1,
    title: '돌담길 끝, 파도 소리만 남은 오후',
    place: '제주, 애월',
    category: '바다',
    date: '2026년 10월',
    excerpt: '창문을 열면 바다가 보이는 작은 집에서 아무 계획 없이 하루를 보냈어요.',
    author: '서윤의 느린 여행',
    avatar: '서',
    image: '/stays/jeju-house.jpeg',
    likes: 128,
    badge: '이번 주 인기',
  },
  {
    id: 2,
    title: '불빛이 켜지는 시간의 부산',
    place: '부산, 광안리',
    category: '도시 산책',
    date: '2026년 9월',
    excerpt: '해 질 무렵 골목을 따라 걷다가 우연히 발견한 동네의 풍경.',
    author: '민호의 주말 기록',
    avatar: '민',
    image: '/stays/busan-living.jpeg',
    likes: 96,
    badge: '',
  },
  {
    id: 3,
    title: '햇살과 책 한 권이면 충분했던 날',
    place: '강원, 양양',
    category: '자연 속으로',
    date: '2026년 9월',
    excerpt: '숲이 가까운 숙소에서 천천히 읽고, 천천히 쉬었던 기록을 남겨요.',
    author: '지우의 쉼표 여행',
    avatar: '지',
    image: '/stays/city-stay.jpeg',
    likes: 74,
    badge: '',
  },
  {
    id: 4,
    title: '제주에서 찾은 나만의 아침 루틴',
    place: '제주, 서귀포',
    category: '혼자 여행',
    date: '2026년 8월',
    excerpt: '빵집에서 커피를 사고, 바다가 보이는 길을 오래 걸었어요.',
    author: '하루의 여행 노트',
    avatar: '하',
    image: '/stays/jeju-house.jpeg',
    likes: 63,
    badge: '',
  },
  {
    id: 5,
    title: '동네 사람처럼 보낸 부산의 이틀',
    place: '부산, 전포동',
    category: '맛집 탐방',
    date: '2026년 8월',
    excerpt: '줄 서서 먹은 국수부터 밤 산책까지, 다시 가고 싶은 코스예요.',
    author: '유나의 골목 지도',
    avatar: '유',
    image: '/stays/busan-living.jpeg',
    likes: 51,
    badge: '',
  },
  {
    id: 6,
    title: '도시를 벗어나 만난 초록빛 주말',
    place: '경기, 가평',
    category: '주말 여행',
    date: '2026년 7월',
    excerpt: '휴대폰을 잠시 내려두고 나무 사이에서 보낸 가벼운 주말.',
    author: '태오의 바깥 생활',
    avatar: '태',
    image: '/stays/city-stay.jpeg',
    likes: 42,
    badge: '',
  },
])

const activeCategory = ref('추천')
const searchTerm = ref('')
const likedPosts = ref([])
const profile = ref(null)
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

onMounted(async () => {
  try {
    profile.value = await fetchCurrentUser({ apiBaseUrl })
  } catch {
    profile.value = null
  }
})

const visiblePosts = computed(() => {
  return filterPosts(posts.value, activeCategory.value, searchTerm.value)
})

function toggleLike(postId) {
  likedPosts.value = likedPosts.value.includes(postId)
    ? likedPosts.value.filter((id) => id !== postId)
    : [...likedPosts.value, postId]
}

function resetFilters() {
  activeCategory.value = '추천'
  searchTerm.value = ''
}
</script>

<template>
  <main class="discover-page">
    <header class="discover-header">
      <a class="discover-brand" href="/" aria-label="모아 홈">
        <span class="brand-symbol" aria-hidden="true"><svg viewBox="0 0 32 32"><path d="M6 24V9l10 10 10-10v15" /></svg></span>
        <span>모아</span>
      </a>

      <label class="discover-search">
        <span class="sr-only">게시글 검색</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.3 4.3"/></svg>
        <input v-model="searchTerm" type="search" placeholder="여행지, 이야기 검색" />
        <span class="search-divider" aria-hidden="true"></span>
        <span class="search-hint">어디로 떠나고 싶나요?</span>
        <span class="search-submit" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.3 4.3"/></svg></span>
      </label>

      <nav class="header-actions" aria-label="계정 메뉴">
        <a class="write-link" href="/login">여행 기록 남기기</a>
        <a v-if="!profile" class="account-button" href="/login" aria-label="Login">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20c.7-3.4 3.4-5.2 8-5.2s7.3 1.8 8 5.2M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z"/></svg>
          <span>로그인</span>
        </a>
        <div v-if="profile" class="account-profile" :aria-label="`${profile.name} profile`">
          <span class="profile-avatar" aria-hidden="true">{{ profile.name.slice(0, 1) }}</span>
          <span class="profile-name">{{ profile.name }}</span>
        </div>
      </nav>
    </header>

    <nav class="category-bar" aria-label="게시글 카테고리">
      <button
        v-for="category in categories"
        :key="category.name"
        class="category-item"
        :class="{ selected: activeCategory === category.name }"
        :aria-pressed="activeCategory === category.name"
        type="button"
        @click="activeCategory = category.name"
      >
        <span class="category-icon" aria-hidden="true">{{ category.icon }}</span>
        <span>{{ category.name }}</span>
      </button>
      <button class="filter-button" type="button" @click="resetFilters">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M7 12h10m-7 6h4"/></svg>
        <span>전체 보기</span>
      </button>
    </nav>

    <section class="discover-main" aria-labelledby="discover-title">
      <div class="section-heading">
        <div>
          <p class="section-eyebrow">다녀온 사람들의 이야기</p>
          <h1 id="discover-title">다음 여행을 먼저 만나보세요</h1>
        </div>
        <button class="map-toggle" type="button" @click="activeCategory = '바다'">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15"/></svg>
          바다 이야기 보기
        </button>
      </div>

      <div v-if="visiblePosts.length" class="post-grid">
        <article v-for="post in visiblePosts" :key="post.id" class="post-card">
          <a class="post-image-link" href="/login" :aria-label="`${post.title} 자세히 보기`">
            <img class="post-image" :src="post.image" :alt="`${post.place} 여행 풍경`" />
            <span v-if="post.badge" class="post-badge">{{ post.badge }}</span>
          </a>
          <button
            class="like-button"
            :class="{ liked: likedPosts.includes(post.id) }"
            type="button"
            :aria-label="likedPosts.includes(post.id) ? `${post.title} 좋아요 취소` : `${post.title} 좋아요`"
            :aria-pressed="likedPosts.includes(post.id)"
            @click="toggleLike(post.id)"
          ><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 8.8c0 4.2-8.8 10-8.8 10s-8.8-5.8-8.8-10a4.6 4.6 0 0 1 8.8-1.9 4.6 4.6 0 0 1 8.8 1.9Z"/></svg></button>
          <div class="post-info">
            <div class="post-title-row"><h2>{{ post.place }}</h2><span class="post-category-chip">{{ post.category }}</span></div>
            <p class="post-title">{{ post.title }}</p>
            <p class="post-excerpt">{{ post.excerpt }}</p>
            <p class="post-date">{{ post.date }} · {{ post.category }}</p>
            <div class="post-author"><span class="author-avatar">{{ post.avatar }}</span><span>{{ post.author }}</span><span class="author-likes">♥ {{ post.likes + (likedPosts.includes(post.id) ? 1 : 0) }}</span></div>
          </div>
        </article>
      </div>

      <div v-else class="empty-state">
        <span aria-hidden="true">⌕</span>
        <h2>찾는 이야기가 아직 없어요</h2>
        <p>다른 검색어나 카테고리를 선택해 보세요.</p>
        <button type="button" @click="searchTerm = ''; activeCategory = '추천'">전체 게시글 보기</button>
      </div>
    </section>

    <footer class="discover-footer">
      <span>© 2026 모아 · 여행의 순간을 모아</span>
      <div><a href="#">개인정보 처리방침</a><a href="#">이용약관</a><a href="#">문의하기</a></div>
    </footer>
  </main>
</template>
