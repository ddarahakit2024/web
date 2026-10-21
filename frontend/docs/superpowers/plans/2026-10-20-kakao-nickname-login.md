# 카카오 닉네임 로그인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 최신 Kakao JavaScript SDK로 닉네임만 동의받아 카카오 ID 기반 로그인을 제공한다.

**Architecture:** Vue는 SDK `Kakao.Auth.authorize()`로 인가 코드 흐름을 시작하고 콜백에서 state를 검증한다. FastAPI는 코드를 카카오 토큰으로 교환하고 사용자 ID/닉네임만 조회해 별도 KakaoAccount 테이블에 저장한 뒤, 기존 앱 JWT 형식으로 토큰을 발급한다.

**Tech Stack:** Vue 3, Vite, Jest, FastAPI, SQLAlchemy, SQLite, Python stdlib `urllib`, Kakao JavaScript SDK v2.8.3.

**Spec:** `frontend/docs/superpowers/specs/2026-10-20-kakao-nickname-login-design.md`

## Global Constraints

- 요청하는 카카오 동의 범위는 `profile_nickname`뿐이며 이메일 필드를 조회하거나 저장하지 않는다.
- 기존 `User` 모델과 로컬 이메일/비밀번호 로그인은 바꾸지 않는다.
- 콜백 URI는 `http://localhost:5173/login/kakao/callback`이다.
- API 응답은 `{code, message, result}` envelope를 따른다.
- 외부 Kakao API 호출은 자동화 테스트에서 실제 네트워크를 사용하지 않는다.

## Review Focus

- 인가 코드 재사용 또는 다른 로그인 흐름과의 섞임: 콜백 state 불일치 테스트와 코드 URL 제거 테스트를 Task 2에서 추가한다.
- 카카오가 거부한 인가 코드: 카카오 인증 실패를 401로 매핑하는 테스트를 Task 1에서 추가한다.
- 카카오 네트워크 장애: 제공자 연결 오류를 502로 매핑하는 테스트를 Task 1에서 추가한다.
- 카카오 프로필에 닉네임이 없거나 형식이 잘못됨: 불완전 프로필 거절 테스트를 Task 1에서 추가한다.
- 이메일이 우연히 포함된 Kakao 응답: KakaoAccount 저장 및 응답에 이메일을 넣지 않는 테스트를 Task 1에서 추가한다.

---

### Task 1: 백엔드 카카오 코드 교환과 계정 로그인

**Files:**
- Create: `app/models/kakao_account.py`
- Modify: `app/models/__init__.py`
- Create: `app/schemas/kakao.py`
- Create: `app/core/kakao.py`
- Create: `app/api/routers/kakao_auth.py`
- Modify: `app/main.py`
- Modify: `app/core/config.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- `KakaoAccount`: `kakao_user_id: str` primary key, `nickname: str`.
- `KakaoLoginRequest`: `code: str`.
- `KakaoProfile`: provider helper returns verified `(kakao_user_id, nickname)`; no email field.
- `POST /user/kakao/login`: accepts `{ "code": "..." }`, responds with existing login result shape and JWT subject `kakao:<id>`.
- Provider helper exchanges the code using configured REST API key and fixed redirect URI, then reads only response `id` and `kakao_account.profile.nickname`.

- [x] **Step 1: Write failing backend tests**
  - Add tests named `test_kakao_login_creates_account_and_returns_kakao_subject`, `test_kakao_login_updates_nickname_for_existing_id`, `test_kakao_login_rejects_invalid_code`, `test_kakao_login_returns_502_when_kakao_is_unavailable`, `test_kakao_login_rejects_profile_without_nickname`, and `test_kakao_login_does_not_store_or_return_email`.
  - Patch the provider helper so no test contacts Kakao.
- [x] **Step 2: Run the focused tests and confirm expected failures**
  - Run: `pytest tests/test_auth.py -q`
  - Expected: the new route/model are missing and the new tests fail for those missing interfaces.
- [x] **Step 3: Implement the model, schema, configuration, Kakao provider helper, and route**
  - Translate provider invalid-code responses to 401 and connection/5xx failures to 502.
  - Upsert by Kakao ID, update nickname, and create JWT with subject `kakao:<id>`.
  - Register the new model before schema creation and include the router in `create_app`.
- [x] **Step 4: Run backend tests**
  - Run: `pytest -q`
  - Expected: all existing and new tests pass.

### Task 2: Vue Kakao SDK and callback handling

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/LoginPage.vue`
- Modify: `frontend/src/style.css`
- Create: `frontend/src/kakaoAuth.mjs`
- Test: `frontend/src/kakaoAuth.test.mjs`

**Interfaces:**
- `beginKakaoLogin({ sdk, key, redirectUri, storage, state })` initializes the SDK once and calls `sdk.Auth.authorize({ redirectUri, scope: 'profile_nickname', state })`.
- `completeKakaoCallback({ search, storage, history, exchangeCode })` validates the stored state, exchanges only a valid code, removes callback query parameters, and returns either a token result or a user-facing error key.
- Login UI receives the app JWT from the backend, stores it in `localStorage.access_token`, and displays a success or error message.

- [x] **Step 1: Write failing Jest tests**
  - Verify the SDK is initialized with the configured key and authorize receives only nickname scope plus redirect URI and state.
  - Verify matching state submits the code and clears callback URL/state.
  - Verify missing/mismatched state never submits the code.
  - Verify Kakao cancellation and backend rejection return distinct error keys.
- [x] **Step 2: Run the focused tests and confirm expected failures**
  - Run: `npm test -- --runTestsByPath src/kakaoAuth.test.mjs`
  - Expected: the helper module is missing.
- [x] **Step 3: Implement the SDK helper and callback integration**
- Load Kakao SDK v2.8.3 using Kakao's documented CDN script and initialize it with `VITE_KAKAO_JAVASCRIPT_KEY`; add the callback path handling.
  - Generate and persist a one-time state before redirect; verify it before sending code to the backend.
  - Provide the requested nickname-only button and accessible loading/error status.
- [x] **Step 4: Run frontend tests and production build**
  - Run: `npm test`
  - Run: `npm run build`
  - Expected: all Jest tests pass and Vite produces a successful build.

### Task 3: Kakao console setup and browser verification

**Files / external settings:**
- Configure Kakao Developers app `mlops` (ID `1614689`): enable Kakao Login, set the consent item to nickname only, register JavaScript SDK domain `http://localhost:5173`, and register redirect URI `http://localhost:5173/login/kakao/callback` for both JavaScript and REST keys.
- Configure local ignored environment values for `VITE_KAKAO_JAVASCRIPT_KEY`, `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET` when enabled, and `KAKAO_REDIRECT_URI` without placing secrets in tracked source files.

- [x] **Step 1: Confirm the browser application runs at `http://localhost:5173/login`**
- [x] **Step 2: Use Chrome DevTools to verify the local login page and callback route load**
- [x] **Step 3: Inspect the Kakao consent request and verify email is absent and nickname is present**
- [x] **Step 4: Complete one authorized Kakao login and verify the app token is saved**
- [x] **Step 5: Run final `npm test`, `npm run build`, and `pytest -q` after console setup**

## Execution Record

- Full backend verification: `15 passed`.
- Full frontend verification: Jest `2 suites / 10 tests passed`; Vite production build succeeded.
- Chrome DevTools verification: the Kakao consent screen requested nickname only; the authorized login returned HTTP 200, displayed the success message, stored the app access token, and removed the callback query string.
- Kakao console required the callback URI on both the JavaScript and REST keys. The REST key's client secret was enabled, so the backend also needs `KAKAO_CLIENT_SECRET` configured.
- Review: no Critical or Important findings. Minor accepted edge case: two simultaneous first-time logins for one Kakao ID can collide on the unique ID insert; a later login succeeds. Existing local accounts remain isolated because Kakao email is not requested or received.
