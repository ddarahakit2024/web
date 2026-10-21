<script setup>
import CourseCard from './CourseCard.vue'

defineProps({ courses: { type: Array, default: () => [] }, title: { type: String, default: '추천 강의' }, savedIds: { type: Array, default: () => [] }, emptyMessage: { type: String, default: '조건에 맞는 강의가 없습니다.' } })
const emit = defineEmits(['select', 'toggle-save'])
</script>

<template>
  <section class="course-grid-section" aria-label="강의 목록">
    <div class="course-grid-section__heading"><h2>{{ title }}</h2><span>{{ courses.length }}개 강의</span><slot name="actions" /></div>
    <div v-if="courses.length" class="course-grid"><CourseCard v-for="course in courses" :key="course.id" :course="course" :saved="savedIds.includes(course.id)" @select="emit('select', $event)" @toggle-save="emit('toggle-save', $event)" /></div>
    <p v-else class="course-grid-section__empty">{{ emptyMessage }}</p>
  </section>
</template>

<style scoped>
.course-grid-section { width: 100%; }
.course-grid-section__heading { display: flex; align-items: baseline; gap: 11px; margin-bottom: 17px; }
.course-grid-section__heading h2 { margin: 0; color: #2c2633; font-size: 22px; font-weight: 700; letter-spacing: -.6px; }
.course-grid-section__heading > span { color: #807887; font-size: 11px; }
.course-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }
.course-grid-section__empty { padding: 45px 16px; border: 1px dashed #d9d1e3; border-radius: 14px; color: #756d7c; font-size: 13px; text-align: center; }
@media (max-width: 880px) { .course-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 17px; } }
@media (max-width: 520px) { .course-grid { grid-template-columns: 1fr; gap: 14px; } }
</style>
