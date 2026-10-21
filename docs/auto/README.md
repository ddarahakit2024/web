# 자동 루프 — 간단 버전

`docs/05-github-이슈-자동화-루프.md`의 핵심만 남긴 구성이다. 루프는 Python 파일 하나다.

```text
[사람] 이슈 작성 + agent:ready 라벨
  → 루프: worktree 생성 → Codex 구현 → verify → Codex 리뷰 → 가드 → 커밋·푸시 → PR
  → [사람] PR 확인 (수정 요청은 `/agent <내용>` 댓글) → 머지
  → 루프: 정리 후 다음 이슈
```

## 파일 (5개)

| 보관본 (`docs/auto/files/`) | 복사할 위치 | 역할 |
| --- | --- | --- |
| `scripts/verify.ps1` | `scripts/verify.ps1` | 완료 기준: pytest + Jest + 빌드 |
| `scripts/agent_loop.py` | `scripts/agent_loop.py` | 루프 전체 |
| `tests/test_agent_loop.py` | `tests/test_agent_loop.py` | 루프의 판단 로직 테스트 |
| `.github/workflows/verify.yml` | `.github/workflows/verify.yml` | PR마다 CI에서 같은 검증 |
| `.github/ISSUE_TEMPLATE/agent-task.yml` | `.github/ISSUE_TEMPLATE/agent-task.yml` | 이슈 양식 (목표 / 완료 기준 / 참고) |

`docs/auto/conftest.py`는 보관본 테스트가 루트 pytest에 섞이지 않게 막는 파일이다. 복사하지 않는다.

## 순서

### 1. git 정리 (1회)
```powershell
git config --global --add safe.directory C:/Users/Playdata/PycharmProjects/ai_backend2
git status          # 미커밋 변경이 있으면 커밋
git remote -v       # GitHub origin이 있는지 확인
```

### 2. 파일 복사 + 커밋
```powershell
Copy-Item docs\auto\files\* . -Recurse -Force
Add-Content .gitignore ".agent-loop/"
powershell -File scripts\verify.ps1      # 마지막 줄이 VERIFY PASS인지 확인
git add -A; git commit -m "chore: 자동 루프 추가"; git push
```

### 3. GitHub 설정 (1회)
```powershell
gh label create agent:ready   --color 0E8A16
gh label create agent:working --color FBCA04
gh label create agent:pr-open --color 1D76DB
gh label create agent:blocked --color B60205
```
그다음 GitHub 저장소의 Settings → Branches → `main` 규칙을 추가한다. PR 필수, 필수 체크는 `verify`로 둔다.

### 4. Codex SDK 설치
```powershell
.\.venv\Scripts\python -m pip install openai-codex
.\.venv\Scripts\python -m pydoc openai_codex     # 이름 확인
```
SDK는 베타라 이름이 바뀔 수 있다. 루프에서 SDK를 쓰는 곳은 `agent_loop.py`의 `ask()` 함수 하나다. 다음 이름이 설치된 SDK와 다르면 이 함수만 고친다: `thread_start`, `thread_resume`, `run`, `Sandbox.workspace_write`, `Sandbox.read_only`, `thread.id`, `final_response`.

### 5. 실행
```powershell
.\.venv\Scripts\python scripts\agent_loop.py     # Ctrl+C로 종료
```
작은 이슈 하나로 먼저 확인한다. 순서는 이렇다: 이슈 작성 → `agent:ready` 라벨 → PR이 생기는지 확인 → `/agent` 댓글로 수정 요청 → 머지 → 다음 이슈로 넘어가는지 확인.

## 동작 규칙

- **이슈 선택**: `agent:ready` 라벨이 있고 `ddarahakit2024`가 작성한 이슈 중 번호가 가장 작은 것.
- **실패 처리**: verify 실패나 리뷰 차단 항목이 생기면 같은 Codex 스레드에 피드백해 다시 시도한다(최대 3회). 그래도 안 되면 `agent:blocked` 라벨과 함께 사유 댓글을 남긴다.
- **가드**: 아래 경우에는 푸시하지 않는다.
  - `.env*`(`.env.example`은 허용), `*.db`, `.github/`, `.codex/`, `scripts/agent_loop.py`를 수정한 경우
  - 변경이 800줄을 넘는 경우
- **사람의 몫**: 머지는 사람만 한다. 루프는 git과 GitHub만 조작하고, Codex는 코드만 고친다.
- **재처리**: 루프가 작업 도중 꺼지면 해당 이슈의 라벨을 `agent:working`에서 `agent:ready`로 직접 되돌린다.
- **기록 위치**: 상태는 `.agent-loop/state.json`, 작업 폴더는 `..\ai_backend2-wt\issue-<번호>`.

## 05 문서에서 뺀 것 (필요해지면 나중에 추가)

Codex 훅, 린트(ruff·eslint), `needs-info`·`pause`·`priority` 라벨, 선행 이슈(`Depends on`) 검사, 테스트 약화 검사, 토큰 상한, 재시작 자동 복구, CI 실패 자동 수정.
