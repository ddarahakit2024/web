<script setup>
defineProps({ images: { type: Array, default: () => [] }, title: { type: String, default: '강의 미리보기' } })
const emit = defineEmits(['select-image'])
function imageFallback(event) { event.target.src = '/course-placeholder.svg' }
</script>

<template>
  <section class="course-gallery" :aria-label="title">
    <button v-for="(image, index) in images.slice(0, 5)" :key="image.src || index" type="button" class="course-gallery__image" :class="{ 'course-gallery__image--main': index === 0, 'course-gallery__image--single': images.length === 1 }" @click="emit('select-image', index)"><img :src="image.src" :alt="image.alt || title + ' ' + (index + 1)" :loading="index ? 'lazy' : 'eager'" @error="imageFallback" /></button>
    <div v-if="!images.length" class="course-gallery__placeholder"><span>MOA CLASS</span><strong>{{ title }}</strong><small>배움의 장면을 미리 만나보세요</small></div>
  </section>
</template>

<style scoped>
.course-gallery { display: grid; grid-template-columns: 1.25fr 1fr 1fr; grid-template-rows: repeat(2, minmax(120px, 1fr)); gap: 8px; min-height: 320px; overflow: hidden; border-radius: 14px; }
.course-gallery__image { min-width: 0; min-height: 0; padding: 0; overflow: hidden; border: 0; background: #f0eaf7; cursor: zoom-in; }
.course-gallery__image img { display: block; width: 100%; height: 100%; object-fit: cover; }
.course-gallery__image--main { grid-row: 1 / 3; }
.course-gallery__image--single { grid-column: 1 / -1; }
.course-gallery__image:focus-visible { outline: 3px solid var(--brand, #5d1eb7); outline-offset: -3px; }
.course-gallery__placeholder { grid-row: 1 / 3; grid-column: 1 / -1; display: flex; flex-direction: column; align-items: flex-start; justify-content: flex-end; gap: 10px; padding: clamp(22px, 5vw, 48px); background: radial-gradient(circle at 82% 20%, #decdf5 0 13%, transparent 13.5%), linear-gradient(140deg, #f1eafb, #e5d8f4 56%, #ccb6e8); color: #342447; }
.course-gallery__placeholder span { padding: 6px 9px; border-radius: 5px; background: #fff9; color: #5d1eb7; font-size: 9px; font-weight: 800; letter-spacing: 1px; }
.course-gallery__placeholder strong { max-width: 16ch; font-size: clamp(24px, 4vw, 38px); letter-spacing: -1.2px; }
.course-gallery__placeholder small { color: #6d5d7d; font-size: 12px; }
@media (max-width: 640px) { .course-gallery { grid-template-columns: 1fr 1fr; grid-template-rows: 220px 100px; gap: 5px; min-height: 0; } .course-gallery__image--main { grid-column: 1 / -1; grid-row: 1; } .course-gallery__image:nth-of-type(n + 4) { display: none; } .course-gallery__placeholder { grid-row: 1 / 3; } }
</style>
