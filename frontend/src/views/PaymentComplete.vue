<script setup>
import { onMounted, ref } from 'vue'
import { confirmPayment } from '../api/paymentApi.js'
import { CoursePageLayout } from '../components/index.js'

const params = new URLSearchParams(window.location.search)
const paymentId = params.get('paymentId')
const failureCode = params.get('code')
const message = ref('결제 결과를 확인하고 있습니다.')
const courseId = ref(null)
const failed = ref(false)

onMounted(async () => {
  if (failureCode) {
    failed.value = true
    message.value = params.get('message') || '결제가 취소되었거나 완료되지 않았습니다.'
    return
  }
  if (!paymentId) {
    failed.value = true
    message.value = '결제 정보를 찾을 수 없습니다. 강의 상세 페이지에서 다시 시도해 주세요.'
    return
  }
  try {
    const order = await confirmPayment(paymentId)
    courseId.value = order.course_id
    message.value = '구매가 완료되었습니다. 이제 강의를 수강할 수 있습니다.'
  } catch (reason) {
    failed.value = true
    message.value = reason?.response?.data?.message || '결제 확인을 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.'
  }
})
</script>

<template>
  <CoursePageLayout active-page="detail">
    <section class="payment-result" :class="{ 'payment-result--error': failed }" aria-live="polite">
      <span class="payment-result__mark" aria-hidden="true">{{ failed ? '!' : '✓' }}</span>
      <p class="payment-result__eyebrow">{{ failed ? 'PAYMENT UPDATE' : 'WELCOME TO THE CLASS' }}</p>
      <h1>{{ failed ? '결제를 완료하지 못했습니다' : courseId ? '수강 신청이 완료되었습니다' : '결제 확인 중' }}</h1>
      <p class="payment-result__message" role="status">{{ message }}</p>
      <a class="payment-result__action" :href="courseId ? '/courses/' + courseId : '/courses'">{{ courseId ? '강의로 이동' : '강의 목록으로' }}</a>
    </section>
  </CoursePageLayout>
</template>

<style scoped>
.payment-result { display: grid; justify-items: center; width: min(540px, 100%); margin: clamp(55px, 12vh, 120px) auto 30px; padding: 42px 28px; border: 1px solid #e8e2ed; border-radius: 16px; background: #fff; text-align: center; }
.payment-result__mark { display: grid; place-items: center; width: 54px; height: 54px; border-radius: 50%; background: #f1eafb; color: #5d1eb7; font-size: 23px; font-weight: 800; }
.payment-result--error .payment-result__mark { background: #fff0f1; color: #a33448; }
.payment-result__eyebrow { margin: 20px 0 0; color: #7144a8; font-size: 9px; font-weight: 800; letter-spacing: 1.4px; }
.payment-result h1 { margin: 9px 0; color: #302a37; font-size: 24px; letter-spacing: -.8px; }
.payment-result__message { max-width: 38ch; margin: 0; color: #756d7c; font-size: 13px; line-height: 1.7; }
.payment-result__action { display: inline-flex; align-items: center; justify-content: center; min-height: 43px; margin-top: 23px; padding: 0 17px; border-radius: 8px; background: #5d1eb7; color: #fff; font-size: 12px; font-weight: 700; text-decoration: none; }
</style>
