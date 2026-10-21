<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({ modelValue: { type: Boolean, default: false }, initialMode: { type: String, default: 'login' }, loading: { type: Boolean, default: false }, error: { type: String, default: '' }, notice: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue', 'submit', 'social-login', 'switch-mode'])
const mode = ref(props.initialMode)
const name = ref('')
const email = ref('')
const password = ref('')
const isSignup = computed(() => mode.value === 'signup')
watch(() => props.initialMode, (value) => { mode.value = value })
watch(() => props.modelValue, (open) => { if (open) mode.value = props.initialMode })
function switchMode(nextMode) { mode.value = nextMode; emit('switch-mode', nextMode) }
function submit() { emit('submit', { mode: mode.value, name: name.value.trim(), email: email.value.trim(), password: password.value }) }
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="course-auth-backdrop" @click.self="emit('update:modelValue', false)" @keydown.esc.prevent="emit('update:modelValue', false)">
      <section class="course-auth" role="dialog" aria-modal="true" aria-labelledby="course-auth-title">
        <header class="course-auth__header"><button class="course-auth__close" type="button" aria-label="닫기" @click="emit('update:modelValue', false)">×</button><h2 id="course-auth-title">{{ isSignup ? '회원가입' : '로그인' }}</h2></header>
        <form class="course-auth__form" @submit.prevent="submit">
          <div class="course-auth__intro"><span aria-hidden="true">M</span><div><h3>{{ isSignup ? '배움의 다음 장을 시작해요' : '다시 만나 반가워요' }}</h3><p>수강 중인 강의를 이어서 학습하세요.</p></div></div>
          <label v-if="isSignup">이름<input v-model="name" type="text" name="name" autocomplete="name" required placeholder="이름을 입력하세요" /></label>
          <label>이메일 주소<input v-model="email" type="email" name="email" autocomplete="email" required placeholder="name@example.com" /></label>
          <label>비밀번호<input v-model="password" :autocomplete="isSignup ? 'new-password' : 'current-password'" type="password" name="password" required :minlength="isSignup ? 8 : 1" :placeholder="isSignup ? '8자 이상 입력하세요' : '비밀번호를 입력하세요'" /></label>
          <p v-if="error" class="course-auth__error" role="alert">{{ error }}</p>
          <p v-if="notice" class="course-auth__notice" role="status">{{ notice }}</p>
          <button class="course-auth__continue" type="submit" :disabled="loading">{{ loading ? '확인 중…' : isSignup ? '계정 만들기' : '로그인' }}</button>
          <p v-if="isSignup" class="course-auth__terms">계정을 만들면 서비스 이용약관과 개인정보 처리방침에 동의하게 됩니다.</p>
        </form>
        <div class="course-auth__divider"><span>또는</span></div>
        <div class="course-auth__social"><button type="button" @click="emit('social-login', 'kakao')"><span aria-hidden="true">K</span> 카카오로 계속하기</button></div>
        <p class="course-auth__switch">{{ isSignup ? '이미 계정이 있나요?' : '처음 오셨나요?' }} <button type="button" @click="switchMode(isSignup ? 'login' : 'signup')">{{ isSignup ? '로그인' : '회원가입' }}</button></p>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.course-auth-backdrop { --course-brand: var(--brand, #5d1eb7); position: fixed; z-index: 1000; inset: 0; display: grid; place-items: center; overflow-y: auto; padding: 24px 14px; background: #20182c70; }
.course-auth { width: min(100%, 430px); overflow: hidden; border: 1px solid #e8e3ec; border-radius: 16px; background: #fff; box-shadow: 0 22px 70px #1b112c40; }
.course-auth__header { position: relative; display: flex; align-items: center; justify-content: center; min-height: 57px; border-bottom: 1px solid #eeeaf1; }
.course-auth__header h2 { margin: 0; color: #2e2934; font-size: 14px; }
.course-auth__close { position: absolute; left: 15px; display: grid; place-items: center; width: 34px; height: 34px; border: 0; border-radius: 50%; background: transparent; color: #403a46; font-size: 25px; cursor: pointer; }
.course-auth__form, .course-auth__social { display: grid; gap: 12px; padding: 23px 25px 0; }
.course-auth__intro { display: flex; align-items: center; gap: 12px; margin-bottom: 5px; }
.course-auth__intro > span { display: grid; place-items: center; width: 41px; height: 41px; border-radius: 12px 12px 12px 3px; background: #f2ebfb; color: var(--course-brand); font-size: 20px; font-weight: 800; }
.course-auth__intro h3 { margin: 0; color: #2e2934; font-size: 18px; letter-spacing: -.5px; }
.course-auth__intro p { margin: 4px 0 0; color: #77717e; font-size: 11px; }
.course-auth__form label { display: grid; gap: 7px; color: #48414e; font-size: 11px; font-weight: 700; }
.course-auth__form input { min-height: 46px; padding: 0 12px; border: 1px solid #dcd6e1; border-radius: 8px; color: #29242f; font: inherit; font-size: 13px; }
.course-auth__form input:focus { border-color: var(--course-brand); outline: 3px solid #5d1eb71a; }
.course-auth__continue { min-height: 47px; border: 0; border-radius: 8px; background: var(--course-brand); color: white; font: inherit; font-size: 13px; font-weight: 700; cursor: pointer; }
.course-auth__continue:hover:not(:disabled) { background: #4d159d; }
.course-auth__continue:disabled { opacity: .6; cursor: wait; }
.course-auth__error { margin: 0; color: #a02b43; font-size: 12px; }
.course-auth__notice { margin: 0; color: #277044; font-size: 12px; }
.course-auth__terms { margin: 0; color: #77717e; font-size: 10px; line-height: 1.5; }
.course-auth__divider { display: flex; align-items: center; gap: 12px; padding: 21px 25px 0; color: #77717e; font-size: 11px; }
.course-auth__divider::before, .course-auth__divider::after { height: 1px; flex: 1; background: #eeeaf1; content: ''; }
.course-auth__social { padding-top: 13px; }
.course-auth__social button { position: relative; min-height: 44px; border: 1px solid #b7b0bd; border-radius: 8px; background: #fff; color: #39333f; font: inherit; font-size: 12px; font-weight: 650; cursor: pointer; }
.course-auth__social button span { position: absolute; left: 15px; color: var(--course-brand); font-size: 15px; font-weight: 800; }
.course-auth__switch { margin: 19px 25px 23px; color: #6e6874; font-size: 11px; text-align: center; }
.course-auth__switch button { padding: 0; border: 0; background: none; color: var(--course-brand); font: inherit; font-weight: 750; text-decoration: underline; cursor: pointer; }
.course-auth button:focus-visible { outline: 3px solid #c9b4e8; outline-offset: 2px; }
@media (max-width: 480px) { .course-auth { border-radius: 12px; } .course-auth__form, .course-auth__social { padding-right: 18px; padding-left: 18px; } .course-auth__divider { padding-right: 18px; padding-left: 18px; } .course-auth__switch { margin-right: 18px; margin-left: 18px; } }
</style>
