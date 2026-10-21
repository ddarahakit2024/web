<script setup>
defineProps({ title: { type: String, required: true }, category: { type: String, default: '' }, instructor: { type: String, default: '' }, summary: { type: String, default: '' } })
const emit = defineEmits(['share', 'save'])
</script>

<template>
  <section class="course-summary">
    <div><span v-if="category" class="course-summary__category">{{ category }}</span><h1>{{ title }}</h1><p>{{ summary }}</p><div class="course-summary__instructor"><span aria-hidden="true">{{ instructor.slice(0, 1) || 'M' }}</span><b>{{ instructor || 'MOA Academy 강사진' }}</b><small>강의 제작자</small></div></div>
    <div class="course-summary__actions"><button type="button" @click="emit('share')"><span aria-hidden="true">↗</span> 공유</button><button type="button" @click="emit('save')"><span aria-hidden="true">♡</span> 저장</button></div>
  </section>
</template>

<style scoped>
.course-summary { --course-brand: var(--brand, #5d1eb7); display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; }
.course-summary__category { display: inline-block; padding: 6px 9px; border-radius: 5px; background: #f1eafb; color: var(--course-brand); font-size: 10px; font-weight: 750; }
.course-summary h1 { max-width: 24ch; margin: 13px 0 7px; color: #2c2633; font-size: clamp(25px, 3.6vw, 38px); line-height: 1.25; letter-spacing: -1.2px; }
.course-summary p { max-width: 65ch; margin: 0; color: #716a78; font-size: 13px; line-height: 1.7; }
.course-summary__instructor { display: flex; align-items: center; gap: 9px; margin-top: 20px; color: #453e4c; font-size: 11px; }
.course-summary__instructor > span { display: grid; place-items: center; width: 31px; height: 31px; border-radius: 50%; background: #eee4f8; color: var(--course-brand); font-size: 13px; font-weight: 750; }
.course-summary__instructor small { color: #8c8492; }
.course-summary__actions { display: flex; gap: 4px; flex: none; }
.course-summary__actions button { padding: 8px; border: 0; border-radius: 7px; background: transparent; color: #51495a; font: inherit; font-size: 11px; cursor: pointer; }
.course-summary__actions button:hover { background: #f1eafb; color: var(--course-brand); }
.course-summary__actions button:focus-visible { outline: 3px solid var(--course-brand); outline-offset: 2px; }
@media (max-width: 600px) { .course-summary { flex-direction: column; gap: 9px; } .course-summary__actions { align-self: flex-end; } }
</style>
