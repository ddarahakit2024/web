<script setup>
import { computed } from 'vue'

const props = defineProps({ course: { type: Object, required: true }, saved: { type: Boolean, default: false } })
const emit = defineEmits(['select', 'toggle-save'])
const image = computed(() => props.course.thumbnail_url || '/course-placeholder.svg')
const price = computed(() => Number(props.course.price_krw || 0).toLocaleString('ko-KR'))
</script>

<template>
  <article class="course-card">
    <a class="course-card__link" :href="`/courses/${course.id}`" @click="emit('select', course)">
      <div class="course-card__image"><img :src="image" :alt="`${course.title || '강의'} 대표 이미지`" loading="lazy" /><span>{{ course.category || 'MOA CLASS' }}</span></div>
      <div class="course-card__body"><div class="course-card__instructor"><span class="course-card__avatar">{{ (course.instructor_name || '강사').slice(0, 1) }}</span>{{ course.instructor_name || '전문 강사' }}</div><h3>{{ course.title || '강의 제목' }}</h3><p>{{ course.summary || '강의 내용을 확인해 보세요.' }}</p><div class="course-card__bottom"><span>강의 전체 보기 <b aria-hidden="true">↗</b></span><strong>₩{{ price }}</strong></div></div>
    </a>
    <button class="course-card__save" type="button" :aria-label="saved ? '관심 강의 해제' : '관심 강의 저장'" :aria-pressed="saved" @click="emit('toggle-save', course)"><span aria-hidden="true">{{ saved ? '♥' : '♡' }}</span></button>
  </article>
</template>

<style scoped>
.course-card { --course-brand: var(--brand, #5d1eb7); position: relative; min-width: 0; overflow: hidden; border: 1px solid #e9e4ed; border-radius: 14px; background: #fff; transition: transform .18s ease, box-shadow .18s ease; }
.course-card:hover { transform: translateY(-3px); box-shadow: 0 13px 30px #32204716; }
.course-card__link { color: inherit; text-decoration: none; }
.course-card__image { position: relative; aspect-ratio: 1.58; overflow: hidden; background: #f0eaf7; }
.course-card__image img { display: block; width: 100%; height: 100%; object-fit: cover; transition: transform .28s ease; }
.course-card:hover .course-card__image img { transform: scale(1.03); }
.course-card__image > span { position: absolute; left: 12px; bottom: 12px; padding: 6px 8px; border-radius: 5px; background: #261d32d9; color: #fff; font-size: 9px; font-weight: 700; }
.course-card__body { padding: 15px 16px 14px; }
.course-card__instructor { display: flex; align-items: center; gap: 7px; color: #756d7c; font-size: 10px; }
.course-card__avatar { display: grid; place-items: center; width: 23px; height: 23px; border-radius: 50%; background: #f1eafb; color: var(--course-brand); font-size: 10px; font-weight: 750; }
.course-card h3 { margin: 11px 0 6px; color: #2c2633; font-size: 15px; font-weight: 700; letter-spacing: -.45px; line-height: 1.45; }
.course-card p { display: -webkit-box; min-height: 36px; margin: 0; overflow: hidden; color: #79717f; font-size: 11px; line-height: 1.6; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.course-card__bottom { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 15px; padding-top: 12px; border-top: 1px solid #f0edf2; }
.course-card__bottom span { color: #817887; font-size: 10px; }
.course-card__bottom span b { color: var(--course-brand); }
.course-card__bottom strong { color: #302938; font-size: 13px; }
.course-card__save { position: absolute; top: 10px; right: 10px; display: grid; place-items: center; width: 35px; height: 35px; border: 0; border-radius: 50%; background: #ffffffde; color: var(--course-brand); font-size: 20px; cursor: pointer; }
.course-card__save[aria-pressed="true"] { background: var(--course-brand); color: white; }
.course-card a:focus-visible, .course-card button:focus-visible { outline: 3px solid var(--course-brand); outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { .course-card, .course-card__image img { transition: none; } }
</style>
