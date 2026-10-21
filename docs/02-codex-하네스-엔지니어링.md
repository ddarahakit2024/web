# 02. Codex 하네스 엔지니어링

## 1. 하네스란

모델 자체는 바꿀 수 없다. 바꿀 수 있는 것은 **모델이 일하는 환경**이다. 같은 모델이라도 아래 요소가 잘 갖춰져 있으면 결과물이 안정적이고, 없으면 매번 운에 맡기게 된다.

| 구성 요소 | 이 프로젝트에서의 실체 | 역할 |
| --- | --- | --- |
| 지시(Instructions) | `AGENTS.md`(루트·폴더별), 역할 에이전트의 `developer_instructions` | 무엇을 지키고 무엇을 하지 말아야 하는지 |
| 지식(Context) | `docs/` 로드맵·spec·ADR·API 계약 | 왜 이렇게 만드는지, 무엇이 이미 결정됐는지 |
| 도구·권한(Tools) | 샌드박스 모드, 승인 정책, 스킬(`.agents/skills`) | 무엇을 실행할 수 있고, 반복 절차를 어떻게 수행하는지 |
| 훅(Hooks) | `.codex/hooks.json` — 도구 실행 직전 거부, 턴 종료 점검 | 규칙을 실행 시점에 기계적으로 강제 |
| 검증(Verification) | pytest, Jest, 빌드, 린트, E2E, 계약 검사를 묶은 **단일 검증 명령** | 에이전트가 "끝났다"고 말할 근거 |
| 피드백(Feedback) | 실패 출력, 리뷰 에이전트 결과 | 다음 시도에서 무엇을 고칠지 |
| 기억(Memory) | 진행 로그, 핸드오프 노트, 교훈 기록 | 세션이 끊겨도 이어서 일할 수 있게 |

핵심 원칙: **에이전트가 스스로 틀렸다는 것을 알 수 있게 만든다.** 사람이 매번 눈으로 확인해야만 오류가 발견되는 구조는 하네스가 부족한 것이다.

---

## 2. 현재 하네스 진단

| # | 문제 | 근거 | 영향 |
| --- | --- | --- | --- |
| 1 | 역할 에이전트 경로가 실제와 다름 | `AGENTS.md`는 `../.codex/agents/*.toml`이라고 하지만 파일은 저장소 안 `.codex/agents/`에 있음 | 새 세션에서 에이전트 정의를 못 찾을 수 있음 |
| 2 | 모델명 메모가 실제 파일과 다름 | `AGENTS.md`는 `gpt-=5.6-Luna`로 잘못 적혀 있다고 하지만 실제 toml은 `gpt-5.6-Luna` | 매번 "실행할 때 고쳐 쓰기"에 의존. **toml 자체를 `gpt-5.6-luna`로 고치고 메모를 삭제**하는 편이 안전 |
| 3 | `sandbox_mode = "Auto"` | Codex의 샌드박스 값은 보통 `read-only` / `workspace-write` / `danger-full-access` | 설치된 Codex 버전에서 유효한 값인지 확인 필요(`codex --help`, 공식 문서) |
| 4 | 스킬이 두 곳에 있고, 하나는 git에 안 올라감 | `skills/api-devloper`와 `.agents/skills/api-devloper` 중복, `.gitignore`에 `.agents/` 포함, 이름 오타 `devloper` | 다른 PC·세션에서 스킬이 사라지고, 두 사본이 어긋남 |
| 5 | 검증 명령이 하나로 묶여 있지 않음 | 루트 `AGENTS.md`는 pytest/Jest만, `frontend/AGENTS.md`는 Playwright 확인을 요구하지만 Playwright 미설치, 빌드 확인 규칙 없음 | 에이전트마다 다른 기준으로 "완료" 판단 |
| 6 | Playwright 규칙과 "서버 직접 실행 금지" 규칙 충돌 | E2E는 서버가 떠 있어야 함 | 에이전트가 규칙 위반 또는 검증 생략 중 하나를 고르게 됨 |
| 7 | 린트·포맷·타입 검사 없음 | ruff/eslint/prettier 설정 없음 | 스타일 흔들림, 리뷰 비용 증가 |
| 8 | 프런트·백엔드 API 계약의 단일 원본이 없음 | spec 문서 문장으로만 합의 | 병렬 개발 시 필드명·형식 불일치 |
| 9 | 문서 위치 분산 | `docs/superpowers/`, `frontend/docs/superpowers/` | 맥락 찾기에 토큰 낭비 |
| 10 | 비밀값 접근 규칙 없음 | 루트 `.env`, `frontend/.env.local`에 실제 키 존재 | 에이전트가 키를 읽어 로그·문서에 노출할 위험 |
| 11 | 테스트가 실제 DB를 건드리지 않는다는 보장이 규칙뿐 | 스킬 문서에만 "app.db 금지" | 실수 시 운영 데이터 손상 |
| 12 | Python 버전 미고정 | `partitioned` 쿠키가 3.14 이상 필요(코드 리뷰 보고서) | 다른 환경에서 테스트 통과·실행 실패 |
| 13 | CI 없음 | `.github/workflows` 없음 | 에이전트가 검증을 건너뛰어도 막을 장치가 없음 |

---

## 3. 목표 하네스 구조

```text
AGENTS.md                      # 짧게: 원칙, 명령어, 금지사항, 문서 지도 (≈100줄 이내)
app/AGENTS.md                  # 백엔드 전용 규칙 (계층, 응답 형식, 마이그레이션, 테스트 픽스처)
frontend/AGENTS.md             # 프런트 전용 규칙 (구조, axios, 상태 표시, 테스트 방식)
.codex/
  config.toml                  # (지원 버전이면) 프로젝트 기본 모델·샌드박스·승인 정책
  hooks.json                   # PreToolUse(브랜치·보호 경로 거부), Stop(턴 종료 점검) — 4.11
  hooks/guard_edit.py, stop_check.py
  agents/
    backend-dev.toml
    frontend-dev.toml
    reviewer.toml              # 신규: 읽기 전용 리뷰어
    qa-e2e.toml                # 신규: E2E 시나리오 작성·실행
.agents/skills/                # git에 포함 (현재 .gitignore에서 제외 필요)
  api-developer/               # 오타 수정
  vue-screen/
  db-migration/
  payment-change/
  release-check/
scripts/
  verify.ps1                   # 단일 검증 게이트 (Windows)
  verify.sh                    # CI(리눅스)용 동일 로직
  agent_loop/                  # GitHub 이슈 → PR 자동 루프 (Python + Codex SDK, 05 문서)
.agent-loop/                   # 루프 상태·로그 (gitignore)
.github/
  ISSUE_TEMPLATE/agent-task.yml  # 목표/맥락/제약/완료 기준 이슈 폼
  pull_request_template.md
docs/
  01~04 ...                    # 이 문서들
  decisions/                   # ADR: 결정 사항
  specs/  plans/               # 기능별 spec·plan (superpowers 폴더 통합)
  api/openapi.json             # FastAPI에서 생성한 계약 스냅샷
  runbooks/                    # 배포·백업 복구·결제 장애 대응
  harness/
    progress.md                # 진행 로그 (세션 간 기억)
    lessons.md                 # 에이전트가 반복한 실수와 그에 대한 하네스 수정
.github/workflows/verify.yml   # PR마다 verify 실행
```

---

## 4. 구성 요소별 설계

### 4.1 AGENTS.md — 짧고, 명령적이고, 검증 가능한 문장만

루트 `AGENTS.md`는 매 세션 맥락에 들어가므로 **길수록 비용이 들고 중요한 규칙이 묻힌다.** 상세 설명은 docs로 빼고 링크만 둔다.

권장 목차(예시):

```markdown
# 프로젝트
단일 강사 온라인 강의 판매 사이트. 로드맵: docs/01-기능-로드맵.md

# 구조
- app/: FastAPI (규칙: app/AGENTS.md)
- frontend/: Vue 3 + Vite (규칙: frontend/AGENTS.md)
- DB: SQLite app.db, 스키마 변경은 Alembic 리비전으로만

# 명령
- 전체 검증: powershell -File scripts/verify.ps1   ← 완료 보고 전 반드시 통과
- 빠른 검증: powershell -File scripts/verify.ps1 -Fast

# 완료의 정의
1. verify 전체 통과 2. 새 동작마다 테스트 추가 3. spec의 검증 항목 충족
4. docs/harness/progress.md에 변경 요약·남은 일 기록

# 금지
- .env, frontend/.env.local 읽기·출력·수정 금지 (.env.example만 수정)
- 테스트에서 app.db 사용 금지, app.db 삭제·초기화 금지
- 기존 테스트를 통과시키려고 테스트 기대값을 바꾸지 말 것 (spec 변경이 있을 때만, 이유를 보고)
- 개발 서버 임의 실행 금지. 직접 띄운 프로세스는 작업 종료 전 종료
- git push, main 브랜치 직접 커밋 금지
- 결제·인증·환불 로직 변경 시 payment-change 스킬 절차를 따를 것

# 결정이 필요한 경우
docs/01-기능-로드맵.md 8절의 결정 항목에 해당하면 구현하지 말고 질문으로 멈춘다.

# 서브에이전트
- 역할 정의: .codex/agents/*.toml (경로는 저장소 루트 기준)
- 백엔드 작업은 backend_dev, 프런트 작업은 frontend_dev, 리뷰는 reviewer
```

작성 요령:
- "가능하면 ~하세요" 대신 "~한다 / ~하지 않는다".
- 규칙마다 **기계적으로 확인 가능한 형태**를 선호한다. 예: "테스트를 잘 작성" ✕ → "새 API마다 성공·검증 실패·권한 없음 테스트 각 1개 이상" ○.
- 반복되는 실수가 생기면 AGENTS.md에 한 줄 추가하기 전에 **테스트·린트 규칙으로 막을 수 있는지** 먼저 본다. 규칙 문장은 무시될 수 있지만 실패하는 테스트는 무시할 수 없다.

### 4.2 폴더별 AGENTS.md

Codex는 작업 중인 경로에 가까운 `AGENTS.md`를 함께 읽는다. 백엔드·프런트 규칙을 분리하면 각 에이전트가 필요한 것만 본다.

`app/AGENTS.md`에 들어갈 내용:
- 계층: router(입출력) → service(비즈니스 규칙, 트랜잭션) → model. 결제 확정처럼 여러 진입점이 공유하는 로직은 service로.
- 응답 형식 `{code, message, result}`, 오류는 `HTTPException` → `app/main.py` 핸들러.
- 외부 연동(PortOne, Kakao, VOD, 이메일)은 `app/integrations/`의 클라이언트로 분리하고 테스트에서는 가짜 구현 주입. 테스트에서 실제 외부 호출 금지.
- 모델 변경 시 Alembic 리비전 생성 + 업그레이드/다운그레이드 테스트.
- 권한이 필요한 API는 비로그인 401, 타인 리소스 404/403, 관리자 전용 403 테스트 필수.

`frontend/AGENTS.md`에 들어갈 내용:
- 폴더: `api, assets, components, router, stores, views` (기존 역할 정의 유지).
- 백엔드 호출은 공통 axios 인스턴스만 사용, 기본 주소 `http://127.0.0.1:8000`.
- 모든 데이터 화면은 로딩 / 빈 상태 / 오류(재시도) / 권한 없음 상태를 구분하고 각각 테스트.
- 가격·권한 판단은 표시용일 뿐 최종 판단은 서버. 프런트에서 금액을 계산해 서버에 보내지 않는다.
- E2E 규칙은 4.6 참고(현재의 "playwright로 확인" 문장은 대체).

### 4.3 역할 에이전트(.codex/agents)

현재 두 정의는 형식이 맞으므로 같은 형식으로 정리·추가한다.

정리할 점:
- `model`을 실제 사용 가능한 이름(`gpt-5.6-luna`)으로 고치고 AGENTS.md의 "실행 시 바꿔 쓰라"는 메모 삭제.
- `sandbox_mode`를 Codex가 지원하는 값으로(구현 에이전트는 `workspace-write`, 리뷰어는 `read-only`).
- `developer_instructions`에 담당 폴더 밖 수정 금지, 완료 전 verify 실행, 결과 보고 형식을 명시.

추가 제안:

```toml
# .codex/agents/reviewer.toml (예시 — 형식은 기존 파일과 동일)
name = "reviewer"
description = "변경분을 spec과 보안 체크리스트 기준으로 검토하는 읽기 전용 리뷰어"
model = "gpt-5.6-luna"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
너는 코드를 수정하지 않는 리뷰어다.
입력: 기능 spec 경로와 git diff 범위.
검토 순서: 1) spec의 완료 기준 충족 여부 2) 인증·권한·결제 금액·IDOR
3) 테스트가 실제 동작을 검증하는지(목 남용, 기대값 완화 여부) 4) 마이그레이션 안전성.
출력: 심각도(차단/권고)별 목록, 각 항목에 파일:줄과 재현 시나리오. 추측은 '확인 필요'로 표시.
"""
```

`qa-e2e`: Playwright 시나리오 작성·실행 담당. 서버 기동·종료 규칙을 지시문에 포함.

> 리뷰는 반드시 **구현한 세션과 다른 새 컨텍스트**에서 한다. 같은 컨텍스트는 자기 결정을 정당화하는 경향이 있다.

### 4.4 스킬(.agents/skills) — 반복 절차를 문서화

스킬은 "이 종류의 일은 이 순서로 한다"는 절차서다. AGENTS.md에 다 넣으면 길어지므로, 특정 작업에서만 필요한 절차를 스킬로 분리한다.

| 스킬 | 언제 | 핵심 절차 |
| --- | --- | --- |
| `api-developer` (기존, 이름 수정) | 백엔드 API 추가·변경 | 기존 내용 유지 + service 계층·OpenAPI 스냅샷 갱신 추가 |
| `vue-screen` | 화면 추가 | 라우트 등록 → api 함수 → 스토어 → 뷰 → 4가지 상태 → Jest |
| `db-migration` | 모델 변경 | 모델 수정 → `alembic revision --autogenerate` → 생성물 검토(SQLite batch) → 데이터 이전 스크립트 → upgrade/downgrade 테스트 → `app.db` 백업 안내 |
| `payment-change` | 결제·환불·수강권 | 상태 전이표 갱신 → 금액은 서버 기준 → 멱등성·동시성 테스트 → PortOne 가짜 클라이언트 시나리오(성공·금액 불일치·네트워크 오류·중복 웹훅) → reviewer 필수 |
| `release-check` | 배포 전 | verify 전체, 마이그레이션 dry-run, 환경변수 체크리스트, 백업 확인, 런북 갱신 |

스킬 작성 요령: `SKILL.md`의 `description`이 언제 써야 하는지 판단 근거가 되므로 트리거 상황을 구체적으로 쓴다.

### 4.5 단일 검증 게이트 — `scripts/verify.ps1`

에이전트·사람·CI가 **같은 명령 하나**로 완료를 판단하게 만든다. 하네스에서 가장 투자 대비 효과가 큰 부분이다.

단계(앞 단계 실패 시 중단, `-Fast`는 1~3만):

| 단계 | 내용 | 실패 시 출력 |
| --- | --- | --- |
| 1 | `ruff check` + `ruff format --check` (app, tests) | 파일:줄과 규칙 |
| 2 | `eslint` + `prettier --check` (frontend/src) | 파일:줄과 규칙 |
| 3 | `pytest -q` | 실패 테스트 이름과 assert 차이 |
| 4 | `npm test` (Jest) | 실패 테스트 이름 |
| 5 | `npm run build` (Vite) | 빌드 오류 |
| 6 | OpenAPI 계약 검사: 앱에서 생성한 스키마와 `docs/api/openapi.json` 비교 | 바뀐 경로·필드 목록 ("의도한 변경이면 스냅샷 갱신") |
| 7 | 마이그레이션 검사: 빈 DB에 `alembic upgrade head` 후 모델과 차이 없음 | 누락된 리비전 |
| 8 | (옵션 `-E2E`) Playwright | 실패 시나리오와 스크린샷 경로 |

설계 규칙:
- **종료 코드로 성공/실패를 명확히**. 마지막 줄에 `VERIFY PASS` / `VERIFY FAIL: <단계>` 출력.
- 실패 출력은 짧게(에이전트 맥락을 실패 로그로 채우지 않도록). 전체 로그는 파일로 저장하고 경로만 출력.
- 테스트는 항상 격리된 DB. `tests/conftest.py`에서 `DATABASE_URL`이 `app.db`를 가리키면 **즉시 실패하는 가드**를 둔다.
- 개발 서버를 띄우지 않는다(8단계만 예외, 4.6).

### 4.6 E2E와 "서버 실행 금지" 규칙의 조정

사용자 선호(서버는 사용자가 실행, 에이전트가 띄운 서버는 종료)를 지키면서 E2E를 돌리는 방법 중 하나를 골라 AGENTS.md에 명시한다.

- **A안(권장)**: E2E 전용 포트(예: 백엔드 8100, 프런트 5180)와 임시 SQLite 파일로 Playwright `webServer`가 직접 띄우고 테스트 후 자동 종료. 사용자의 8000/5173 개발 서버와 충돌하지 않는다. 이 경우에도 프런트의 API 주소는 환경변수로만 바꾸고 소스 기본값 `http://127.0.0.1:8000`은 유지.
- B안: 사용자가 서버를 띄웠을 때만 `-E2E`를 실행하고, 서버가 없으면 E2E는 "건너뜀"으로 보고.

외부 연동(PortOne 결제창, 카카오, VOD)은 E2E에서 실제로 호출하지 않는다. 백엔드에 테스트 전용 가짜 클라이언트를 주입하는 설정(`APP_ENV=e2e`)을 둔다. 실제 결제창 확인은 사용자의 수동 점검 항목으로 남긴다.

E2E 핵심 시나리오(최대 5~7개로 유지):
1. 가입 → 로그인 → 로그아웃
2. 강의 상세 → 결제(가짜) → 내 강의실에 강의 표시
3. 수강권 없는 사용자의 플레이어 접근 차단, 미리보기 레슨은 재생
4. 레슨 재생 위치 저장 → 재접속 후 이어보기
5. 관리자: 강의 생성 → 공개 → 카탈로그 노출
6. 환불 승인 → 재생 차단

### 4.7 API 계약 우선(Contract-first)

프런트·백엔드 에이전트를 병렬로 돌리려면 둘이 같은 계약을 봐야 한다.

1. spec 단계에서 엔드포인트·요청·응답 예시를 확정해 `docs/specs/<기능>.md`에 적는다.
2. 백엔드가 먼저 스키마(Pydantic)와 라우터 시그니처를 만들고 `docs/api/openapi.json`을 갱신한다.
3. 프런트는 그 스냅샷 기준으로 api 함수와 목 응답을 만든다.
4. verify 6단계가 계약 변화를 감지한다. 의도치 않은 응답 필드 변경을 자동으로 잡는다.

### 4.8 권한·샌드박스·비밀값

- 구현 에이전트: `workspace-write`, 네트워크는 필요할 때만(패키지 설치 등). 승인 정책은 "요청 시"로 두고 위험 명령은 사람이 승인.
- 리뷰 에이전트: `read-only`.
- 비밀값: `.env`는 에이전트가 읽지 않는다는 규칙 + `.env.example`을 항상 최신으로. 결제 키는 테스트 키만 로컬에 두고, 운영 키는 배포 서버에만.
- 되돌리기 어려운 작업 목록을 AGENTS.md에 명시: `app.db` 삭제·초기화, 마이그레이션 downgrade를 실제 DB에 실행, git 히스토리 재작성, 외부 서비스(PortOne·VOD) 설정 변경.

### 4.9 기억 — 세션이 끊겨도 이어지게

서브에이전트 상태는 세션 간 유지되지 않는다(현재 AGENTS.md에도 명시). 그래서 기억은 **파일**에 둔다.

- `docs/harness/progress.md`: 작업 카드별로 "상태 / 브랜치 / 마지막 verify 결과 / 남은 일 / 막힌 이유"를 에이전트가 갱신. 새 세션은 이 파일부터 읽는다.
- `docs/harness/lessons.md`: 에이전트가 틀린 패턴과 그에 대해 바꾼 하네스(테스트·규칙·스킬)를 날짜와 함께 기록.
- `docs/decisions/`: 사용자가 내린 결정. 에이전트가 같은 질문을 반복하지 않게.

### 4.10 CI — 최후의 방어선

에이전트가 verify를 건너뛰고 "완료"라고 말해도, PR에서 `scripts/verify.sh`가 돌면 걸러진다. GitHub Actions에서 Python·Node 버전을 고정해 "내 PC에서는 됨" 문제를 없앤다. `main` 브랜치는 CI 통과 + 사람 승인 후에만 병합.

자동 루프(05 문서)를 쓰면 CI는 더 중요해진다. 루프가 로컬에서 verify를 돌리더라도, 사람이 머지 버튼을 누르기 전에 깨끗한 환경에서 한 번 더 검증되어야 한다. 브랜치 보호 규칙에서 **CI 통과를 머지 필수 조건**으로 설정하고, 루프가 쓰는 토큰에는 Workflows·Administration 권한을 주지 않아 루프가 CI나 보호 규칙을 바꿀 수 없게 한다.

### 4.11 Codex 훅 — 브랜치 강제와 턴 종료 점검

훅은 Codex가 도구를 실행하기 직전·직후나 턴이 끝날 때 우리 스크립트를 실행하게 하는 장치다. 규칙 문장(AGENTS.md)은 무시될 수 있지만 훅은 **실행 시점에 기계적으로 막는다.** 대화형 세션과 자동 루프(05 문서) 모두에 같은 규칙을 적용할 수 있다.

> 공식 문서도 훅을 "완전한 강제 경계가 아닌 유용한 안전장치"로 설명한다. 샌드박스, 루프의 diff 가드, CI를 **대체하지 않고 그 안쪽에 한 겹 더하는 것**이다.

#### 브랜치 정책 — 방법 B: 자동 생성하지 않고, main에서의 수정을 거부해 Codex가 만들게 한다

`UserPromptSubmit`에서 브랜치를 자동 생성하는 방법(A)은 질문만 하는 대화에도 브랜치가 생기고, 프롬프트 앞부분으로 지은 이름의 품질이 낮다. 그래서 **수정 직전에 검사하고, 조건이 맞지 않으면 이유와 함께 거부**한다. Codex는 거부 사유를 읽고 작업 내용을 이해한 상태에서 직접 브랜치를 만든 뒤 다시 시도한다.

`PreToolUse` 훅(`guard_edit.py`) 판정 규칙:

| 조건 | 판정 | 거부 사유 문구(예) |
| --- | --- | --- |
| 파일 수정 도구(`apply_patch`, 파일을 쓰는 셸 명령)인데 현재 브랜치가 `main`/`master` | deny | "main에서는 수정할 수 없습니다. `git switch -c agent/<이슈번호 또는 날짜>-<영문-요약>`으로 작업 브랜치를 만든 뒤 다시 시도하세요." |
| detached HEAD | deny | "브랜치가 없는 상태입니다. 작업 브랜치를 만드세요." |
| 브랜치 이름이 `agent/`, `feat/`, `fix/`, `docs/`, `chore/`로 시작하지 않음 | deny | "브랜치 이름 규칙: agent/·feat/·fix/·docs/·chore/ 접두사" |
| 수정 대상이 `.env*`(`.env.example` 제외), `*.db`, `.github/workflows/`, `.codex/`, `.agents/`, `scripts/agent_loop/` | deny | "보호된 경로입니다. 필요하면 수정하지 말고 이유를 보고하세요." |
| 셸 명령이 `git push`, `git reset --hard`, `git checkout main`/`git switch main` 후 수정, `rm`/`del` + `app.db`, `alembic downgrade` | deny | "되돌리기 어려운 명령입니다. 사람에게 요청하세요." |
| 셸 명령이 개발 서버 실행(`uvicorn`, `npm run dev`, `vite`, `python main.py`) — E2E 스크립트(H-8)는 예외 | deny | "개발 서버는 사용자가 직접 실행합니다." |
| 그 외 | 허용 | - |

- 읽기 도구·읽기 전용 명령(`git status`, `pytest`)은 브랜치와 무관하게 허용한다. 브랜치 생성 명령(`git switch -c`, `git checkout -b`) 자체는 `main`에서도 허용해야 한다.
- 셸 명령이 "파일을 쓰는지" 완벽히 판별할 수는 없다. 명확한 패턴(리다이렉션 `>`, `sed -i`, `Set-Content`, `Out-File`, `New-Item`, `mv`, `cp`)만 잡고, 나머지는 Stop 점검과 diff 가드가 받친다.
- 훅은 저장소 루트를 `git rev-parse --show-toplevel`로 구한다. 실행 시 작업 디렉터리는 가정하지 않는다.

#### 턴 종료 점검 — `Stop` 훅(`stop_check.py`)

`Stop`은 **턴마다** 실행되므로 변경이 있을 때만 점검한다.

```text
1. git status로 작업 트리 변경 확인 → 마지막 점검 이후 변경 없으면 통과
   (마지막 점검 상태: .agent-loop/hook-state.json에 diff 해시 저장)
2. 점검 항목
   - 현재 브랜치가 main이 아님
   - verify -Fast 통과 (린트 + pytest + Jest. 빌드·E2E는 제외 → 시간 상한 안에)
   - 보호 경로 변경 없음
   - app/ 또는 frontend/src/ 소스가 바뀌었으면 tests/ 또는 *.test.mjs도 바뀌었는지
   - docs/harness/progress.md 갱신 여부 (변경이 있는 경우)
3. 실패 → {"decision": "block", "reason": "<실패 항목과 로그 요약 30줄 이내>"}
   Codex는 reason을 다음 지시로 받아 이어서 수정한다
4. 입력의 stop_hook_active가 true(이미 한 번 이어서 진행한 턴)이면 다시 block하지 않고
   실패 내용만 .agent-loop/logs/에 기록 후 통과 → 무한 반복 방지
```

- **최종 판정은 훅이 아니다.** 전체 `verify`는 자동 루프의 Python과 CI가 실행한다. 훅은 "Codex가 끝났다고 말하기 전에 한 번 더 고치게 하는" 역할이다.
- `SessionEnd`는 제한 시간이 1~3초라 점검에 쓸 수 없다.

#### 설정 형태 (스케치 — 구현은 H-11)

```json
// .codex/hooks.json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "^(apply_patch|Bash)$",
        "hooks": [{ "type": "command", "command": "python .codex/hooks/guard_edit.py", "timeout": 10 }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "python .codex/hooks/stop_check.py", "timeout": 300 }] }
    ]
  }
}
```

- 셸 도구의 실제 이름은 Codex 버전마다 다를 수 있다. 처음에는 입력 JSON의 `tool_name`을 로그로 남기는 훅으로 확인한 뒤 matcher를 확정한다.
- 훅 스크립트 자체의 단위 테스트를 `tests/hooks/`에 둔다(입력 JSON → 기대 판정). 훅이 잘못 막거나 통과시키면 모든 작업이 영향을 받기 때문이다.

#### 신뢰(trust)와 운영 주의

- 저장소 훅은 `/hooks`에서 **검토·신뢰해야 실행**되며, 신뢰는 파일 해시에 묶인다. **훅 파일을 바꾸면 다시 신뢰할 때까지 조용히 건너뛴다.** 훅을 수정한 뒤에는 반드시 `/hooks`에서 다시 신뢰한다.
- 훅 파일은 `.codex/` 아래에 있으므로 `PreToolUse` 규칙과 루프 diff 가드로 Codex의 수정을 막는다. 훅 변경은 사람이 대화형으로만 한다.
- SDK(app-server)로 실행할 때도 훅이 적용되는지는 공식 문서에 명시되어 있지 않다. 자동 루프는 시작할 때 훅 동작을 **자가 점검**한다(05 문서 2절).

---

## 5. 하네스 정비 작업 목록 (기능 개발보다 먼저)

| ID | 작업 | 완료 기준 |
| --- | --- | --- |
| H-1 | 에이전트 정의 정리: 모델명·샌드박스 값 수정, 경로 메모 수정, reviewer 추가 | 새 세션에서 세 에이전트 생성 성공 |
| H-2 | 스킬 정리: `skills/` 중복 제거, `.agents/skills`를 git 추적, 이름 오타 수정 | `git ls-files .agents/skills`에 스킬 파일 존재 |
| H-3 | 린트·포맷 도입(ruff, eslint, prettier) + 기존 코드 일괄 정리(별도 커밋) | 린트 0건 |
| H-4 | `scripts/verify.ps1`/`verify.sh` 작성, `tests/conftest.py`에 app.db 가드 | `verify` 한 번으로 1~5단계 실행, 가드 테스트 존재 |
| H-5 | AGENTS.md 재작성(루트 축약 + `app/`·`frontend/` 분리), 문서 폴더 통합 | 루트 AGENTS.md 약 100줄 이내, 기존 규칙 누락 없음 |
| H-6 | CI 워크플로, Python·Node 버전 고정 | PR에서 verify 자동 실행 |
| H-7 | OpenAPI 스냅샷·계약 검사 (Alembic 도입 후 마이그레이션 검사 추가) | 응답 필드를 바꾸면 verify 실패 |
| H-8 | Playwright 도입(4.6 A안) — P0 기능이 어느 정도 생긴 뒤 | 시나리오 1개 이상 통과, 종료 후 남은 프로세스 없음 |
| H-9 | GitHub 준비: 라벨, 이슈 템플릿, PR 템플릿, `main` 브랜치 보호(CI 필수·직접 푸시 금지), 미커밋 변경 정리, git `safe.directory` | 템플릿으로 이슈 생성 가능, `main` 직접 푸시 거부됨 |
| H-10 | 자동 루프 `scripts/agent_loop/` 구현(05 문서) + 루프 자체의 pytest(gh·Codex·verify를 가짜로 대체) | 테스트 이슈 1건이 PR까지 생성되고, 머지 후 다음 이슈를 선택 |
| H-11 | Codex 훅(4.11): `PreToolUse` 브랜치·보호 경로·위험 명령 거부, `Stop` 턴 종료 점검, 훅 단위 테스트, `/hooks` 신뢰 등록 | main에서 파일 수정 시도 → 거부 후 Codex가 브랜치 생성, `verify -Fast` 실패 상태로 턴 종료 시 이어서 수정, 훅 테스트 통과 |

H-1~H-6은 서로 작고 독립적이라 한 번에 하나씩 기능 루프(03 문서)로 처리한다. H-11은 H-4(verify) 이후 언제든 가능하며, H-10보다 먼저 하면 루프 구현 작업 자체도 훅의 보호를 받는다. **H-1~H-11은 자동 루프가 기대는 하네스이므로 루프로 돌리지 않고 Codex와 대화형으로 진행한다.**
