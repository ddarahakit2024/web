<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({ keyword: { type: String, default: '' }, category: { type: String, default: '' }, categories: { type: Array, default: () => [] } })
const emit = defineEmits(['search', 'update:keyword', 'update:category'])
const form = reactive({ keyword: props.keyword, category: props.category })
watch(() => props.keyword, (value) => { form.keyword = value })
watch(() => props.category, (value) => { form.category = value })
function submit() {
  emit('update:keyword', form.keyword)
  emit('update:category', form.category)
  emit('search', { keyword: form.keyword.trim(), category: form.category })
}
</script>

<template>
  <form class="course-search" role="search" @submit.prevent="submit">
    <label class="course-search__keyword"><span>무엇을 배우고 싶나요?</span><input v-model="form.keyword" type="search" placeholder="예: 데이터 분석, UX 디자인" /></label>
    <label class="course-search__category"><span>분야</span><select v-model="form.category"><option value="">전체 분야</option><option v-for="item in categories" :key="item" :value="item">{{ item }}</option></select></label>
    <button type="submit" aria-label="강의 검색"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/></svg><span>강의 검색</span></button>
  </form>
</template>

<style scoped>
.course-search { --course-brand: var(--brand, #5d1eb7); display: grid; grid-template-columns: 1fr 220px auto; align-items: center; gap: 0; padding: 8px; border: 1px solid #e7e1ed; border-radius: 15px; background: white; box-shadow: 0 7px 23px #3220470c; }
.course-search label { display: grid; gap: 5px; min-width: 0; padding: 8px 16px; }
.course-search label + label { border-left: 1px solid #ece7f0; }
.course-search label span { color: #332b3b; font-size: 11px; font-weight: 750; }
.course-search input, .course-search select { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: #6e6576; font: inherit; font-size: 12px; }
.course-search input:focus-visible, .course-search select:focus-visible { outline: 2px solid var(--course-brand); outline-offset: 3px; border-radius: 3px; }
.course-search button { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 48px; padding: 0 17px; border: 0; border-radius: 10px; background: var(--course-brand); color: white; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.course-search button:hover { background: #4d159d; }
.course-search button:focus-visible { outline: 3px solid #c9b4e8; outline-offset: 2px; }
.course-search svg { width: 17px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
@media (max-width: 600px) { .course-search { grid-template-columns: 1fr auto; border-radius: 12px; } .course-search label { padding: 9px 10px; } .course-search label + label { grid-column: 1; border-top: 1px solid #ece7f0; border-left: 0; } .course-search button { grid-column: 2; grid-row: 1 / 3; min-height: 44px; padding: 0 13px; } .course-search button span { display: none; } }
</style>
