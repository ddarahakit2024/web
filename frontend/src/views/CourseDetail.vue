<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCourse } from '../api/courseApi.js'
import { confirmPayment, createPaymentOrder } from '../api/paymentApi.js'
import { launchPortOnePayment } from '../api/coursePayment.js'
import { CourseGallery, CoursePageLayout, CoursePurchaseCard, CourseSummary } from '../components/index.js'
import { getCoursePageState, getCourseStateView, getCourseTitle } from '../stores/courseViewModel.js'

const props = defineProps({ courseId: { type: [Number, String], default: null } })
const course = ref(null)
const loading = ref(true)
const missing = ref(false)
const error = ref('')
const purchasing = ref(false)
const purchased = ref(false)
const purchaseMessage = ref('')
const purchaseNeedsLogin = ref(false)
const purchaseError = ref(false)
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || undefined
const invalidCourseId = computed(() => !Number.isSafeInteger(props.courseId) || props.courseId < 1)
const pageState = computed(() => getCoursePageState({ loading: loading.value, error: error.value, missing: missing.value, course: course.value, detail: true }))
const stateView = computed(() => getCourseStateView(pageState.value, true))
const courseImages = computed(() => course.value?.thumbnail_url ? [{ src: course.value.thumbnail_url, alt: `${getCourseTitle(course.value)} 강의 이미지` }] : [])

async function loadCourse() {
  if (invalidCourseId.value) { loading.value = false; return }
  loading.value = true; error.value = ''; missing.value = false
  try { course.value = await fetchCourse(props.courseId, { apiBaseUrl }) } catch (reason) { missing.value = reason?.response?.status === 404; if (!missing.value) error.value = '강의 정보를 불러오지 못했습니다.' } finally { loading.value = false }
}

async function buyCourse() {
  if (purchasing.value || purchased.value || !course.value) return
  purchasing.value = true; purchaseMessage.value = ''; purchaseNeedsLogin.value = false; purchaseError.value = false
  try {
    const order = await createPaymentOrder(course.value.id, { apiBaseUrl })
    const paymentResult = await launchPortOnePayment(order)
    if (paymentResult?.code !== undefined) { purchaseError.value = true; purchaseMessage.value = paymentResult.message || '결제가 취소되었거나 완료되지 않았습니다.'; return }
    await confirmPayment(order.payment_id, { apiBaseUrl })
    purchased.value = true; purchaseMessage.value = '구매가 완료되었습니다. 이제 강의를 수강할 수 있습니다.'
  } catch (reason) {
    purchaseError.value = true; purchaseNeedsLogin.value = reason?.response?.status === 401
    purchaseMessage.value = purchaseNeedsLogin.value ? '로그인 후 강의를 구매할 수 있습니다.' : reason?.response?.data?.message || '결제를 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally { purchasing.value = false }
}

function shareCourse() { if (typeof navigator !== 'undefined' && navigator.share) navigator.share({ title: course.value?.title, url: window.location.href }) }
onMounted(() => { if (invalidCourseId.value) loading.value = false; else loadCourse() })
</script>

<template>
  <CoursePageLayout active-page="detail">
    <section v-if="invalidCourseId" class="course-state" role="alert"><h1>올바르지 않은 강의 ID입니다.</h1><p>강의 목록에서 다른 강의를 선택해 주세요.</p><a class="course-link-button" href="/courses">강의 목록 보기</a></section>
    <p v-else-if="pageState === 'loading'" class="course-state" role="status">{{ stateView.message }}</p>
    <section v-else-if="pageState === 'missing'" class="course-state" role="alert"><h1>{{ stateView.message }}</h1><p>강의 목록에서 다른 강의를 선택해 주세요.</p><a class="course-link-button" href="/courses">강의 목록 보기</a></section>
    <div v-else-if="pageState === 'error'" class="course-state" role="alert"><p>{{ error || stateView.message }}</p><button class="course-link-button" type="button" @click="loadCourse">다시 시도</button></div>
    <article v-else class="course-detail-page">
      <a class="course-back-link" href="/courses">← 강의 목록</a>
      <CourseSummary :title="getCourseTitle(course)" :category="course.category" :instructor="course.instructor_name" :summary="course.summary" @share="shareCourse" />
      <CourseGallery :images="courseImages" :title="getCourseTitle(course)" />
      <div class="course-detail-layout">
        <section class="course-description">
          <h2>강의 소개</h2><p>{{ course.description || course.summary }}</p>
          <h2>커리큘럼</h2>
          <ol v-if="course.curriculum?.length" class="course-curriculum"><li v-for="section in course.curriculum" :key="section.title"><strong>{{ section.title }}</strong><ul><li v-for="lesson in section.lessons" :key="lesson">{{ lesson }}</li></ul></li></ol>
          <p v-else class="course-curriculum-empty">커리큘럼을 준비하고 있습니다.</p>
          <p v-if="purchaseMessage" class="course-purchase-message" :class="{ 'course-purchase-message--error': purchaseError }" role="status" aria-live="polite">{{ purchaseMessage }} <a v-if="purchaseNeedsLogin" href="/login">로그인하기</a></p>
        </section>
        <CoursePurchaseCard :price="course.price_krw" :purchasing="purchasing" :purchased="purchased" @purchase="buyCourse" />
      </div>
    </article>
  </CoursePageLayout>
</template>

<style scoped>
.course-detail-page { display: grid; gap: 22px; padding: 29px 0 15px; }
.course-back-link { width: fit-content; color: #776e80; font-size: 11px; text-decoration: none; }.course-back-link:hover { color: #5d1eb7; }
.course-detail-layout { display: grid; grid-template-columns: minmax(0, 1fr) 325px; align-items: start; gap: 35px; margin-top: 4px; }
.course-description { max-width: 760px; color: #6f6876; font-size: 13px; line-height: 1.85; }.course-description h2 { margin: 20px 0 8px; color: #302a37; font-size: 19px; letter-spacing: -.5px; }.course-description > p { margin: 0; white-space: pre-line; }
.course-curriculum { display: grid; gap: 12px; padding-left: 20px; }.course-curriculum > li { padding: 15px 17px; border: 1px solid #ece7f0; border-radius: 10px; background: white; }.course-curriculum strong { color: #362e40; }.course-curriculum ul { display: grid; gap: 5px; margin: 8px 0 0; padding-left: 17px; color: #79717f; font-size: 11px; }.course-curriculum-empty { padding: 14px 16px; border: 1px dashed #d9d1e3; border-radius: 10px; }
.course-purchase-message { margin-top: 17px !important; padding: 12px 14px; border-radius: 8px; background: #f2ebfb; color: #553181; font-size: 12px; }.course-purchase-message--error { background: #fff1f2; color: #9a354b; }.course-purchase-message a { margin-left: 6px; color: #5d1eb7; font-weight: 700; }
.course-state { min-height: 300px; display: grid; align-content: center; justify-items: center; gap: 8px; color: #736b7b; font-size: 13px; text-align: center; }.course-state h1 { margin: 0; color: #302a37; font-size: 22px; }.course-state p { margin: 0; }.course-link-button { display: inline-flex; align-items: center; justify-content: center; min-height: 40px; margin-top: 10px; padding: 0 15px; border: 0; border-radius: 8px; background: #5d1eb7; color: #fff; font: inherit; font-size: 12px; font-weight: 700; text-decoration: none; cursor: pointer; }
@media (max-width: 760px) { .course-detail-page { gap: 16px; padding-top: 18px; }.course-detail-layout { grid-template-columns: 1fr; gap: 24px; } }
</style>
