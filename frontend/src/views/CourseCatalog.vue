<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCourses } from '../api/courseApi.js'
import { CourseGrid, CoursePageLayout, CourseSearchBar } from '../components/index.js'
import { getCoursePageState, getCourseStateView } from '../stores/courseViewModel.js'

const courses = ref([])
const loading = ref(true)
const error = ref('')
const keyword = ref('')
const category = ref('')
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || undefined
const categories = computed(() => [...new Set(courses.value.map((course) => course.category).filter(Boolean))])
const filteredCourses = computed(() => courses.value.filter((course) => {
  const query = keyword.value.trim().toLocaleLowerCase()
  const matchesCategory = !category.value || course.category === category.value
  const searchable = `${course.title || ''} ${course.summary || ''} ${course.instructor_name || ''}`.toLocaleLowerCase()
  return matchesCategory && (!query || searchable.includes(query))
}))
const pageState = computed(() => getCoursePageState({ loading: loading.value, error: error.value, courses: courses.value }))
const stateView = computed(() => getCourseStateView(pageState.value))

async function loadCourses() {
  loading.value = true
  error.value = ''
  try { courses.value = await fetchCourses({ apiBaseUrl }) } catch { error.value = '강의 목록을 불러오지 못했습니다.' } finally { loading.value = false }
}

function search(criteria) { keyword.value = criteria.keyword; category.value = criteria.category }
onMounted(loadCourses)
</script>

<template>
  <CoursePageLayout active-page="catalog">
    <section class="catalog-hero">
      <div class="catalog-hero__copy"><span>LEARN AT YOUR PACE</span><h1>다음 가능성을<br /><em>배움으로 시작하세요</em></h1><p>현장에서 바로 쓰이는 지식을, 원하는 속도로 배워보세요.</p></div>
      <div class="catalog-hero__shape" aria-hidden="true"><span>MOA<br />CLASS</span><i></i><b></b></div>
      <CourseSearchBar v-model:keyword="keyword" v-model:category="category" :categories="categories" @search="search" />
    </section>
    <section class="catalog-content" aria-labelledby="catalog-title">
      <div class="catalog-title"><div><p>YOUR NEXT CHAPTER</p><h2 id="catalog-title">지금 시작할 수 있는 강의</h2></div><span v-if="!loading">{{ filteredCourses.length }}개 강의</span></div>
      <p v-if="pageState === 'loading'" class="catalog-state" role="status">{{ stateView.message }}</p>
      <div v-else-if="pageState === 'error'" class="catalog-state" role="alert"><p>{{ error || stateView.message }}</p><button type="button" @click="loadCourses">다시 시도</button></div>
      <p v-else-if="pageState === 'empty'" class="catalog-state">{{ stateView.message }}</p>
      <CourseGrid v-else :courses="filteredCourses" :title="category || '모든 강의'" :empty-message="'검색 조건에 맞는 강의가 없습니다. 다른 키워드를 입력해 보세요.'" />
    </section>
  </CoursePageLayout>
</template>

<style scoped>
.catalog-hero { position: relative; display: grid; grid-template-columns: 1fr 260px; align-items: center; gap: 12px 28px; margin: 30px 0 39px; padding: clamp(25px, 5vw, 52px); overflow: hidden; border-radius: 18px; background: linear-gradient(118deg, #f5f0fc, #f2ecfa 58%, #e8ddf5); }
.catalog-hero__copy { position: relative; z-index: 1; }
.catalog-hero__copy > span, .catalog-title > div > p { color: #6b38a9; font-size: 9px; font-weight: 800; letter-spacing: 1.4px; }
.catalog-hero h1 { margin: 12px 0 9px; color: #30253c; font-size: clamp(31px, 4.4vw, 51px); font-weight: 650; letter-spacing: -2px; line-height: 1.2; }
.catalog-hero h1 em { color: #5d1eb7; font-style: normal; }
.catalog-hero__copy > p { margin: 0; color: #6f6679; font-size: 12px; line-height: 1.7; }
.catalog-hero__shape { position: relative; display: grid; place-items: center; width: 210px; height: 165px; justify-self: center; border-radius: 46% 54% 53% 47% / 54% 40% 60% 46%; background: #d6c3ee; color: #56328a; transform: rotate(-6deg); }
.catalog-hero__shape span { position: relative; z-index: 1; font-size: 19px; font-weight: 850; letter-spacing: -1px; line-height: 1.05; text-align: center; transform: rotate(6deg); }
.catalog-hero__shape i, .catalog-hero__shape b { position: absolute; border: 1px solid #9e7acb; border-radius: 50%; }
.catalog-hero__shape i { inset: 17px 25px; transform: rotate(32deg); }.catalog-hero__shape b { inset: 30px 10px; transform: rotate(-30deg); }
.catalog-hero :deep(.course-search) { grid-column: 1 / -1; position: relative; z-index: 2; }
.catalog-content { padding: 0 0 12px; }
.catalog-title { display: flex; align-items: flex-end; justify-content: space-between; gap: 14px; margin: 0 0 18px; }
.catalog-title > div > p { margin: 0 0 7px; }.catalog-title h2 { margin: 0; color: #2d2635; font-size: 22px; letter-spacing: -.8px; }.catalog-title > span { color: #827a89; font-size: 11px; }
.catalog-state { padding: 55px 16px; color: #736b7b; font-size: 13px; text-align: center; }.catalog-state button { margin-top: 9px; padding: 10px 16px; border: 0; border-radius: 7px; background: #5d1eb7; color: white; cursor: pointer; }
@media (max-width: 700px) { .catalog-hero { grid-template-columns: 1fr; margin-top: 18px; padding: 24px 18px; } .catalog-hero__shape { position: absolute; top: 7px; right: -65px; width: 165px; height: 140px; opacity: .45; } .catalog-hero__copy { min-height: 165px; } .catalog-hero :deep(.course-search) { grid-column: 1; } .catalog-title h2 { font-size: 18px; } }
</style>
