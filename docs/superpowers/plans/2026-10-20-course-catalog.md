# 강의 카탈로그 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 수강생이 온라인 강의 목록과 각 강의의 상세 정보 및 가격을 조회할 수 있게 한다.

**Architecture:** FastAPI는 SQLAlchemy 강의 모델을 SQLite에서 읽어 표준 응답 봉투로 공개한다. Vue는 Axios로 목록/상세 API를 호출하고 현재 경로에 따라 카탈로그 또는 상세 화면을 표시한다. 백엔드와 프런트엔드는 각각 별도 worktree와 역할 에이전트에서 구현하고 마지막에 합쳐 전체 검증한다.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, SQLite, Vue 3, Axios, Jest, pytest

**Spec:** `docs/superpowers/specs/2026-10-20-course-catalog-design.md`

## Global Constraints

- 강의 데이터는 SQLAlchemy 모델로 SQLite `app.db`에 저장한다.
- 공개 조회 경로는 `GET /courses`와 `GET /courses/{course_id}`다.
- 성공/오류 응답은 `{code, message, result}` 형식을 따른다.
- API 기본 주소는 `http://127.0.0.1:8000`이며 `VITE_API_BASE_URL` 설정을 우선 사용한다.
- 기존 `/login` 화면 및 인증 흐름을 유지한다.
- 이번 범위는 조회 전용이며 결제, 수강 등록, 강의 작성 화면/API, 권한 기능을 추가하지 않는다.
- 개발 서버를 실행하지 않는다. 백엔드는 전체 `pytest`, 프런트엔드는 전체 Jest suite를 통과시킨다.

## Review Focus

- 비어 있는 카탈로그: `GET /courses`는 오류 대신 빈 배열과 200을 반환한다.
- 존재하지 않는 ID: 상세 API는 표준 404 봉투를, 화면은 목록 복귀 동작을 제공한다.
- 잘못된 ID 형식: 숫자 ID가 아닌 요청은 일관된 422 봉투를 반환한다.
- API 실패: 화면은 로딩을 끝내고 재시도 가능한 오류 상태를 표시한다.
- 이미지가 로드되지 않음: 카드와 상세 정보의 텍스트/가격 조회가 막히지 않도록 대체 이미지를 보여준다.

---

## Shared API Contract

- `GET /courses` 성공 결과: `{code: 200, message: string, result: CourseListItem[]}`
- `GET /courses/{course_id}` 성공 결과: `{code: 200, message: string, result: CourseDetail}`
- 404 결과: `{code: 404, message: string, result: null}`
- `CourseListItem`: `{id: number, title: string, instructor_name: string, category: string, price_krw: number, thumbnail_url: string, summary: string}`
- `CourseDetail`: `CourseListItem`의 모든 속성과 `description: string`, `curriculum: Array<{title: string, lessons: string[]}>`
- 목록 정렬: `display_order` 오름차순, 동률이면 `id` 오름차순.

## Worktree Setup

- 기존 사용자의 미커밋 변경을 보존한다. worktree 기반은 해당 변경을 포함한 작업 시작 시점 스냅샷으로 만들고, `.env`와 SQLite DB 파일은 스냅샷에 넣지 않는다.
- `course-backend`와 `course-frontend` worktree를 별도로 만든다. 각 에이전트는 지정 폴더만 수정한다.
- 프런트엔드 에이전트는 API 계약에 의존하는 부분을 위 Shared API Contract 그대로 사용한다.
- 통합은 공통 스냅샷 기준으로 두 작업 diff를 현재 작업 폴더에 적용해 기존 미커밋 변경과 보존한다.

## Task 1: Backend course read API

**Owner:** backend role agent in `course-backend` worktree

**Files:**
- Create: `app/models/course.py`
- Modify: `app/models/__init__.py`
- Create: `app/schemas/course.py`
- Create: `app/api/routers/courses.py`
- Modify: `app/main.py`
- Create: `tests/test_courses.py`

**Interfaces:**
- Produces `CourseListItem`, `CourseDetail`, `GET /courses`, and `GET /courses/{course_id}` exactly as defined in Shared API Contract.
- SQLAlchemy `Course` fields: `id`, `title`, `instructor_name`, `category`, `price_krw`, `thumbnail_url`, `summary`, `description`, `curriculum` (JSON list), `display_order`.

- [ ] **Step 1: Write failing API tests** in `tests/test_courses.py` using an isolated in-memory SQLite engine and the existing `create_app(test_session, create_schema=False)` pattern. Cover empty list, populated list ordered by `display_order` then `id`, list fields, detail fields including curriculum, missing numeric ID 404 envelope, and non-numeric ID 422 envelope.
- [ ] **Step 2: Run the new test module** with `pytest tests/test_courses.py -q`; confirm failures are due to missing course routes/model.
- [ ] **Step 3: Implement the model, schemas, router, and app registration.** Use SQLAlchemy JSON for curriculum, Pydantic response models with the shared field names, and the existing response envelope/HTTP error handlers.
- [ ] **Step 4: Run backend verification** with `pytest`; all tests pass.
- [ ] **Step 5: Commit backend changes** in the backend worktree with message `feat: add course catalog read API`.

## Task 2: Frontend course catalog and detail screens

**Owner:** frontend role agent in `course-frontend` worktree

**Files:**
- Create: `frontend/src/courseApi.js`
- Create: `frontend/src/courseViewModel.js`
- Create: `frontend/src/CourseCatalog.vue`
- Create: `frontend/src/CourseDetail.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/package.json` and `frontend/package-lock.json` to add Axios
- Create: `frontend/src/courseApi.test.mjs`
- Create: `frontend/src/coursePage.test.mjs`

**Interfaces:**
- Consumes the Shared API Contract and the backend's two GET routes.
- `courseApi.js` exports `fetchCourses({apiBaseUrl})` and `fetchCourse(courseId, {apiBaseUrl})`, returning the server's `result` values and propagating request/HTTP errors.
- `courseViewModel.js` exports `resolveCourseRoute(pathname)`, `formatCoursePrice(priceKrw)`, and presentation helpers consumed by both Vue screens; Jest tests these helpers with real API-shaped data.
- `/` and `/courses` show the catalog; `/courses/:id` shows detail; `/login` continues to render the existing login page.

- [ ] **Step 1: Write failing Jest tests** for Axios API URL/default base handling and list/detail result extraction in `courseApi.test.mjs`; test route resolution, API-shaped card/detail presentation, KRW formatting, empty/loading/error/404 states, and image fallback behavior in `coursePage.test.mjs`. Mock Axios at the API boundary, not page-state helpers.
- [ ] **Step 2: Run the focused Jest tests** with `npm test -- --runTestsByPath src/courseApi.test.mjs src/coursePage.test.mjs`; confirm failures reflect missing course API/screens.
- [ ] **Step 3: Implement the Axios API module, view-model helpers, and Vue screens.** Preserve `/login`; load and render list/detail states; format integer KRW prices for Korean locale; provide a fallback image and list navigation for missing courses. Keep the tested view-model helpers as the source of the displayed card/detail values.
- [ ] **Step 4: Run frontend verification** with `npm test` and `npm run build`; both pass.
- [ ] **Step 5: Commit frontend changes** in the frontend worktree with message `feat: add course catalog screens`.

## Integration

- [ ] Confirm both worktrees are based on the same user-change snapshot and both task commits touch only their assigned areas.
- [ ] Apply backend and frontend changes to the shared working tree without discarding pre-existing user modifications.
- [ ] Run `pytest` at the repository root and `npm test` plus `npm run build` in `frontend`.
- [ ] Inspect the final diff and report any checks that cannot run; do not start either development server.
