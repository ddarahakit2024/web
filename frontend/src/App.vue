<script setup>
import LoginPage from './views/LoginPage.vue'
import CourseCatalog from './views/CourseCatalog.vue'
import CourseDetail from './views/CourseDetail.vue'
import PaymentComplete from './views/PaymentComplete.vue'
import { isPaymentCompleteRoute, resolveCourseRoute } from './router/index.js'

const route = resolveCourseRoute(window.location.pathname)
const isPaymentComplete = isPaymentCompleteRoute(window.location.pathname)
</script>

<template>
  <PaymentComplete v-if="isPaymentComplete" />
  <LoginPage v-else-if="route.name === 'login'" />
  <CourseDetail v-else-if="route.name === 'detail'" :course-id="route.id" />
  <CourseCatalog v-else />
</template>
