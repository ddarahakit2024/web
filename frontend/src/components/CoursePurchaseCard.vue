<script setup>
import { computed } from 'vue'

const props = defineProps({ price: { type: Number, required: true }, purchasing: { type: Boolean, default: false }, purchased: { type: Boolean, default: false }, disabled: { type: Boolean, default: false } })
const emit = defineEmits(['purchase'])
const formattedPrice = computed(() => `₩${Number(props.price || 0).toLocaleString('ko-KR')}`)
</script>

<template>
  <aside class="course-purchase" aria-label="강의 수강 신청">
    <p class="course-purchase__eyebrow">강의 구매</p><p class="course-purchase__price">{{ formattedPrice }} <span>1회 결제</span></p>
    <ul><li>구매 후 바로 수강 시작</li><li>모바일과 PC에서 학습</li><li>강의 자료 포함</li></ul>
    <button type="button" :disabled="disabled || purchasing || purchased" :aria-busy="purchasing" @click="emit('purchase')">{{ purchasing ? '결제창을 여는 중…' : purchased ? '수강 등록 완료' : '강의 구매하기' }}</button>
    <p class="course-purchase__note">안전한 결제 후 내 강의에서 학습할 수 있어요.</p>
  </aside>
</template>

<style scoped>
.course-purchase { --course-brand: var(--brand, #5d1eb7); position: sticky; top: 96px; width: min(100%, 340px); padding: 22px; border: 1px solid #e8e2ed; border-radius: 14px; background: #fff; box-shadow: 0 9px 28px #32204710; }
.course-purchase__eyebrow { margin: 0 0 8px; color: #79717f; font-size: 11px; font-weight: 700; }
.course-purchase__price { margin: 0; color: #2d2635; font-size: 24px; font-weight: 800; letter-spacing: -.8px; }
.course-purchase__price span { color: #817987; font-size: 11px; font-weight: 450; letter-spacing: 0; }
.course-purchase ul { display: grid; gap: 11px; margin: 18px 0 20px; padding: 16px 0 0; border-top: 1px solid #eeeaf1; list-style: none; }
.course-purchase li { position: relative; padding-left: 21px; color: #5d5565; font-size: 11px; }
.course-purchase li::before { position: absolute; left: 0; color: var(--course-brand); content: '✓'; font-weight: 800; }
.course-purchase button { width: 100%; min-height: 47px; border: 0; border-radius: 8px; background: var(--course-brand); color: #fff; font: inherit; font-size: 12px; font-weight: 750; cursor: pointer; }
.course-purchase button:hover:not(:disabled) { background: #4d159d; }
.course-purchase button:disabled { opacity: .58; cursor: not-allowed; }
.course-purchase button:focus-visible { outline: 3px solid #c9b4e8; outline-offset: 2px; }
.course-purchase__note { margin: 12px 0 0; color: #8a8290; font-size: 10px; line-height: 1.6; text-align: center; }
@media (max-width: 760px) { .course-purchase { position: static; width: 100%; } }
</style>
