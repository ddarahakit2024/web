# 05. GitHub 이슈 기반 자동 개발 루프 (Python + Codex SDK)

> 이 문서는 **설계서**다. 아래 코드는 구조를 설명하는 스케치이며, 실제 구현은 작업 카드 H-9·H-10(04 문서)으로 Codex에게 맡긴다.

## 1. 목표 동작

```text
 [사람] 이슈 작성 + agent:ready 라벨
            │
            ▼
 ┌─ 루프(Python, 사용자 PC에서 상시 실행) ───────────────────────────┐
 │ ① 다음 이슈 선택 → ② worktree·브랜치 생성 → ③ Codex 구현            │
 │ → ④ verify(루프가 직접 실행) → ⑤ Codex 리뷰(읽기 전용, 새 스레드)    │
 │ → ⑥ diff 가드 검사 → ⑦ 커밋·푸시 → ⑧ PR 생성 → ⑨ PR 상태 감시         │
 └──────────────────────────────────────────────────────────────────┘
            │
            ▼
 [사람] PR 확인 → (수정 요청 시 /agent 댓글 → 루프가 같은 스레드로 수정·푸시)
            │
            ▼
 [사람] 머지 → 이슈 자동 종료(Closes #N) → 루프가 정리 후 ① 로 돌아가 다음 이슈
```

핵심 원칙
- **한 번에 이슈 하나.** 열린 에이전트 PR이 머지(또는 닫힘)되어야 다음 이슈로 넘어간다. 다음 이슈는 항상 최신 `main`에서 시작하므로 충돌이 거의 없다.
- **Codex는 코드만 고친다. git·GitHub 조작은 루프(Python)가 한다.** 커밋·푸시·PR은 결정적인 코드로 처리해야 실수가 없고, Codex에 GitHub 권한을 줄 필요가 없다.
- **완료 판정은 Codex의 말이 아니라 루프가 직접 돌린 `verify` 결과로 한다.**
- **머지는 항상 사람이 한다.** 루프에는 머지 권한을 주지 않는다. 이것이 03 문서의 "사람 개입 지점"을 지키는 장치다.

---

## 2. 사전 준비 (사람이 1회)

| 항목 | 내용 |
| --- | --- |
| 하네스 | H-1~H-6 완료. 특히 `scripts/verify.ps1`이 없으면 이 루프를 켜지 않는다. |
| Python SDK | `pip install openai-codex` (Python 3.10+). SDK는 빠르게 바뀌므로 `requirements-agent.txt`에 **버전 고정**. 인증은 기존 Codex 로그인을 재사용. |
| GitHub CLI | `gh` 로그인(현재 `ddarahakit2024` 계정으로 로그인되어 있음). 장기적으로는 이 저장소 전용 fine-grained 토큰(Contents·Pull requests·Issues 쓰기, Administration·Workflows 권한 없음) 권장. |
| 브랜치 보호 | `main`: 직접 푸시 금지, PR 필수, CI(verify) 통과 필수. 머지는 사람만. |
| 라벨 생성 | 4절의 라벨 목록 |
| 이슈 템플릿 | `.github/ISSUE_TEMPLATE/agent-task.yml` (5절) |
| git 소유권 | 현재 `.git` 폴더 소유자가 `CodexSandboxOffline` 계정이라 일반 계정에서 `dubious ownership` 오류가 난다. 루프를 돌릴 계정에서 `git config --global --add safe.directory C:/Users/Playdata/PycharmProjects/ai_backend2` 1회 실행 또는 폴더 소유권 정리. |
| Codex 훅 | H-11의 `.codex/hooks.json`을 `/hooks`에서 신뢰 등록. 훅 파일을 바꿀 때마다 다시 신뢰해야 한다(해시 기반, 미신뢰 시 조용히 건너뜀). |
| 훅 자가 점검 | 루프 시작 시 1회: 브랜치 없는 임시 worktree(`git worktree add --detach <경로> origin/main`)에서 Codex에게 "README에 한 줄 추가" 턴을 실행 → 훅이 거부하고 파일이 그대로인지 확인. 거부되지 않으면 "훅 비활성" 경고를 로그와 GitHub(선택: 고정 이슈 댓글)에 남기고, Python diff 가드만으로 계속 진행. 점검 후 임시 worktree 삭제. |
| 미커밋 변경 정리 | 현재 작업 트리에 커밋되지 않은 결제 기능 등이 있다. 루프는 `origin/main` 기준 worktree를 쓰므로, 시작 전에 이 변경을 커밋·머지해 두어야 한다. |

---

## 3. 구성

```text
scripts/agent_loop/
  __main__.py        # 진입점: python -m scripts.agent_loop
  config.py          # 저장소, 라벨 이름, 상한값, 모델·추론 강도
  github.py          # gh CLI 래퍼 (이슈·라벨·댓글·PR 조회/생성)
  workspace.py       # git worktree 생성·정리, 커밋·푸시
  agent.py           # Codex SDK 호출 (구현 스레드, 리뷰 스레드, 수정 턴)
  verify.py          # scripts/verify.ps1 실행, 실패 로그 요약
  guards.py          # diff 가드 (금지 경로, 테스트 약화, 크기 상한)
  state.py           # .agent-loop/state.json 읽기/쓰기
  prompts/
    implement.md     # 구현 지시 템플릿
    review.md        # 리뷰 지시 템플릿
    fix.md           # verify 실패·리뷰·PR 피드백 반영 템플릿
.agent-loop/         # gitignore 대상: state.json, 실행 로그, worktree 경로 기록
```

`scripts/agent_loop/`는 하네스 코드이므로 **루프 자신이 처리하는 이슈에서는 수정 금지 경로**로 둔다(6절 가드). 루프 개선은 사람이 Codex와 대화형으로 한다.

---

## 4. 이슈 상태 = 라벨

GitHub 라벨이 상태의 원본이다. 루프가 재시작돼도 라벨을 보고 이어갈 수 있다.

| 라벨 | 붙이는 주체 | 의미 |
| --- | --- | --- |
| `agent:ready` | 사람 | 처리 대상. 사람이 내용 검토(=spec 승인)를 마쳤다는 뜻 |
| `agent:working` | 루프 | 구현 중 |
| `agent:pr-open` | 루프 | PR 올라감, 사람 검토 대기 |
| `agent:needs-info` | 루프 | Codex가 결정 필요 항목을 발견. 질문 댓글을 남김. 사람이 답하고 `agent:ready`로 되돌리면 재처리 |
| `agent:blocked` | 루프 | 재시도 상한 초과. 원인 요약 댓글을 남김 |
| `agent:pause` | 사람 | 열린 이슈 중 하나라도 이 라벨이 있으면 루프가 새 작업을 시작하지 않음(긴급 정지) |
| `risk:high` | 사람 | 결제·인증·환불·마이그레이션. PR 본문에 경고와 수동 확인 목록을 강조, 리뷰 라운드 상한 상향 |
| `priority:p0` / `p1` / `p2` | 사람 | 선택 순서 |

**다음 이슈 선택 규칙**
1. 열린 이슈 중 `agent:ready` + 작성자가 저장소 소유자(`ddarahakit2024`)인 것만.
2. 본문의 `Depends on #N`이 모두 닫혀 있어야 함.
3. `priority:p0 → p1 → p2`, 같은 우선순위는 이슈 번호 오름차순.

> 작성자를 소유자로 제한하는 이유: 공개 저장소라면 누구나 이슈를 쓸 수 있고, 이슈 본문은 그대로 Codex 프롬프트가 된다. 다른 사람이 쓴 이슈·댓글은 **프롬프트 인젝션 경로**다. PR 피드백 댓글도 소유자 것만 읽는다.

---

## 5. 이슈 템플릿

기존 프롬프트 형식(목표/맥락/제약/검증)을 GitHub 이슈 폼으로 옮긴다. 04 문서의 카드 하나 = 이슈 하나.

```yaml
# .github/ISSUE_TEMPLATE/agent-task.yml (스케치)
name: 에이전트 작업
description: Codex 자동 루프가 처리할 작업
labels: []            # agent:ready는 검토 후 사람이 직접 붙인다
body:
  - type: input
    id: card
    attributes: { label: 카드 ID, placeholder: "E-1" }
  - type: textarea
    id: goal
    attributes: { label: 목표 }
    validations: { required: true }
  - type: textarea
    id: context
    attributes: { label: 맥락, description: "참고 문서·코드 경로, 관련 ADR" }
  - type: textarea
    id: constraints
    attributes: { label: 제약 }
  - type: textarea
    id: done
    attributes: { label: 완료 기준, description: "테스트로 확인 가능한 문장으로" }
    validations: { required: true }
  - type: textarea
    id: out_of_scope
    attributes: { label: 범위 밖 }
  - type: textarea
    id: deps
    attributes: { label: 선행 이슈, placeholder: "Depends on #12" }
```

큰 기능은 이슈를 바로 구현용으로 쓰지 말고 **spec 이슈 → (사람 승인) → 구현 이슈** 두 장으로 나눈다. spec 이슈의 결과물은 `docs/specs/*.md`를 추가하는 PR이고, 머지되면 구현 이슈의 맥락에 그 spec을 링크한다. 이렇게 하면 03 문서의 "spec 승인" 관문이 PR 머지로 자연스럽게 구현된다.

---

## 6. 이슈 1건 처리 절차

### ① 선택·착수
- 라벨 `agent:ready` → `agent:working`, 이슈에 "작업 시작" 댓글.
- `state.json`에 `{issue, branch, worktree, thread_id: null, attempts: 0}` 기록.

### ② 작업 공간
```text
git fetch origin
git worktree add ../ai_backend2-wt/issue-<N> -b agent/issue-<N>-<slug> origin/main
(worktree 안에서) 의존성 설치: pip install -r requirements.txt, npm ci (frontend)
```
- 사용자가 작업하는 원래 폴더와 분리되므로 사용자의 개발 서버·미커밋 변경과 섞이지 않는다.
- worktree에는 `.env`가 없다(gitignore). 테스트가 `.env` 없이 통과해야 한다는 하네스 원칙과 일치한다.
- 의존성 설치는 네트워크가 필요하므로 Codex가 아닌 루프가 한다. Codex가 의존성을 추가했다면 ④ 전에 루프가 재설치한다.

### ③ 구현 (Codex 스레드 1)
- `cwd`를 worktree로, 샌드박스는 `workspace_write`.
- 지시: `prompts/implement.md` + 이슈 본문 + `AGENTS.md`(자동으로 읽힘).
- **구조화된 결과**를 `output_schema`로 강제해 루프가 분기할 수 있게 한다.

```json
{
  "status": "done | needs_decision | blocked",
  "summary": "변경 요약",
  "tests_added": ["tests/test_x.py::test_y"],
  "manual_checks": ["로그인 후 /my/courses에서 ...가 보인다"],
  "questions": ["환불 기준 진도율은?"],
  "commit_title": "feat: ..."
}
```
- `needs_decision` → 질문을 이슈 댓글로 남기고 `agent:needs-info`, worktree 정리, 다음 이슈로.
- `blocked` → `agent:blocked` + 사유 댓글.

훅과의 관계: worktree는 이미 `agent/issue-<N>-<slug>` 브랜치이므로 `PreToolUse` 브랜치 검사는 통과하고, 보호 경로·위험 명령 거부만 작동한다. `Stop` 훅이 켜져 있으면 Codex는 `verify -Fast`가 통과할 때까지(최대 한 번 이어서) 스스로 고친 뒤 턴을 끝내므로, ④의 재시도가 줄어든다.

### ④ 검증 (루프가 직접)
- worktree에서 `scripts/verify.ps1` 실행. Codex가 "통과했다"고 해도, `Stop` 훅이 통과시켰어도 다시 돌린다(훅은 빠른 검사만 하고, 비활성일 수도 있다).
- 실패 시 마지막 50줄 정도를 요약해 **같은 스레드**에 `fix.md`로 다음 턴 실행. 상한 3회. 초과하면 `agent:blocked`.

### ⑤ 리뷰 (Codex 스레드 2 — 새 컨텍스트)
- 같은 worktree, 샌드박스 `read_only`, 리뷰어 지시(`prompts/review.md` = `.codex/agents/reviewer.toml`의 지시와 동일 내용).
- 입력: 이슈 본문 + `git diff origin/main...HEAD`.
- 결과 스키마: `{"blocking": [{file, line, reason}], "advisory": [...]}`.
- `blocking`이 있으면 구현 스레드에 전달해 수정 → ④부터 반복. 리뷰 라운드 상한 2회(`risk:high`는 3회).
- `advisory`는 PR 본문에 그대로 싣는다.

### ⑥ diff 가드 (루프가 기계적으로 검사)
하나라도 걸리면 푸시하지 않고 `agent:blocked`.

| 검사 | 이유 |
| --- | --- |
| 금지 경로 변경: `.env*`(단 `.env.example` 허용), `*.db`, `.github/workflows/`, `scripts/agent_loop/`, `.codex/`, `.agents/`, `AGENTS.md` | 비밀값·운영 DB·검증 장치·하네스 자기 수정 방지 |
| 기존 테스트에서 `assert` 줄 삭제, `skip`/`xfail`/`.only`/`.skip` 추가 | "테스트를 약화시켜 통과" 방지 |
| 변경 줄 수 상한(예: 800줄) | 리뷰 불가능한 PR 방지 → 이슈 분할 요청 댓글 |
| 이슈 범위 밖 폴더 변경(예: 프런트 이슈인데 `app/` 변경) | 범위 이탈 |

하네스 자체를 바꾸는 이슈(예: AGENTS.md 개선)는 루프에 넣지 않고 사람이 대화형으로 처리한다.

### ⑦ 커밋·푸시 (루프)
```text
git add -A
git commit -m "<commit_title> (#N)" -m "<summary>" -m "Refs #N"
git push -u origin agent/issue-<N>-<slug>
```
- 커밋은 기능 단위 1개로 충분하다(PR에서 squash merge 권장).

### ⑧ PR 생성 (루프)
`gh pr create --base main --head agent/issue-<N>-<slug> --title ... --body-file ...`

PR 본문 템플릿:
```markdown
Closes #N

## 변경 요약
<summary>

## 검증
- verify: PASS (pytest N개, Jest N개, build OK) — 실행 시각, 시도 횟수
- 추가된 테스트: ...

## 리뷰 에이전트
- 차단 항목: 0 (라운드 N회)
- 권고: ...

## 사람이 확인할 것
- [ ] <manual_checks 목록>
- [ ] (risk:high) 실제 결제창/로그인/영상 재생 수동 확인

## 피드백 방법
수정이 필요하면 이 PR에 `/agent <요청 내용>` 댓글을 남기면 루프가 반영해 푸시합니다.
```
- 라벨 `agent:working` → `agent:pr-open`, 이슈에 PR 링크 댓글.
- CI(verify)가 PR에서 다시 돈다 — 루프 PC 환경과 무관한 두 번째 확인.

### ⑨ PR 감시 (폴링)
`state.json`의 현재 PR을 주기적으로(예: 2분) 조회한다.

| PR 상태 | 루프 동작 |
| --- | --- |
| 머지됨 | worktree 제거, 로컬 브랜치 삭제, `state.current` 비움 → **다음 이슈 선택** (이슈는 `Closes #N`으로 자동 종료) |
| 머지 없이 닫힘 | 이슈에서 `agent:pr-open` 제거, "PR이 닫혀 중단" 댓글, 정리 후 다음 이슈 |
| 소유자의 새 `/agent ...` 댓글 또는 Changes requested 리뷰 | 저장된 `thread_id`로 구현 스레드를 재개(`thread_resume`) → 피드백 전달 → ④~⑦ 반복 → 같은 브랜치에 추가 커밋 푸시 → 처리 완료 댓글 |
| CI 실패 | CI 로그 요약을 피드백으로 위와 동일하게 처리(상한 2회) |
| 대기 | 아무것도 하지 않음 |

이미 처리한 댓글 ID는 `state.json`에 기록해 중복 반영을 막는다.

---

## 7. 코드 스케치

### 7.1 Codex SDK 호출부 (`agent.py`)

2026-10 기준 공식 Python SDK(`openai-codex`)의 공개 API: `Codex()`, `codex.thread_start(cwd=, sandbox=, model=, developer_instructions=, approval_mode=, ...)`, `codex.thread_resume(thread_id, ...)`, `thread.run(input, effort=, output_schema=, sandbox=, ...)` → `TurnResult(status, error, final_response, items, usage, ...)`. 베타 단계라 이름이 바뀔 수 있으므로 구현 시 `help(Codex)` / `python -m pydoc openai_codex`로 설치 버전의 시그니처를 확인한다.

```python
import json
from pathlib import Path

from openai_codex import Codex, Sandbox

PROMPTS = Path(__file__).parent / "prompts"
MODEL = "gpt-5.6-luna"

IMPLEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"enum": ["done", "needs_decision", "blocked"]},
        "summary": {"type": "string"},
        "tests_added": {"type": "array", "items": {"type": "string"}},
        "manual_checks": {"type": "array", "items": {"type": "string"}},
        "questions": {"type": "array", "items": {"type": "string"}},
        "commit_title": {"type": "string"},
    },
    "required": ["status", "summary", "tests_added", "manual_checks", "questions", "commit_title"],
    "additionalProperties": False,
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "blocking": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
        "advisory": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
    },
    "required": ["blocking", "advisory"],
    "additionalProperties": False,
    "$defs": {"finding": {
        "type": "object",
        "properties": {"file": {"type": "string"}, "line": {"type": "integer"}, "reason": {"type": "string"}},
        "required": ["file", "line", "reason"],
        "additionalProperties": False,
    }},
}


def _parse(result) -> dict:
    if result.error is not None or not result.final_response:
        raise AgentError(f"turn failed: {result.status} {result.error}")
    return json.loads(result.final_response)


def implement(codex: Codex, worktree: Path, issue_md: str) -> tuple[str, dict]:
    thread = codex.thread_start(
        cwd=str(worktree),
        sandbox=Sandbox.workspace_write,
        model=MODEL,
        developer_instructions=(PROMPTS / "implement.md").read_text(encoding="utf-8"),
        # approval_mode: 무인 실행이므로 사람 승인을 기다리며 멈추지 않는 모드여야 한다.
        # 기본값(auto_review)의 동작과 선택 가능한 값을 설치 버전에서 확인 후 지정.
    )
    result = thread.run(issue_md, effort="medium", output_schema=IMPLEMENT_SCHEMA)
    return thread.id, _parse(result)  # 스레드 ID 속성 이름은 설치 버전에서 확인


def fix(codex: Codex, worktree: Path, thread_id: str, feedback: str) -> dict:
    thread = codex.thread_resume(thread_id, cwd=str(worktree), sandbox=Sandbox.workspace_write)
    prompt = (PROMPTS / "fix.md").read_text(encoding="utf-8").format(feedback=feedback)
    return _parse(thread.run(prompt, effort="medium", output_schema=IMPLEMENT_SCHEMA))


def review(codex: Codex, worktree: Path, issue_md: str, diff: str) -> dict:
    thread = codex.thread_start(
        cwd=str(worktree),
        sandbox=Sandbox.read_only,
        model=MODEL,
        developer_instructions=(PROMPTS / "review.md").read_text(encoding="utf-8"),
        ephemeral=True,  # 리뷰 스레드는 재개할 일이 없다
    )
    prompt = f"## 이슈\n{issue_md}\n\n## 변경 사항\n```diff\n{diff}\n```"
    return _parse(thread.run(prompt, effort="high", output_schema=REVIEW_SCHEMA))
```

### 7.2 메인 루프 (`__main__.py`)

```python
POLL_SECONDS = 120
MAX_VERIFY_ATTEMPTS = 3
MAX_REVIEW_ROUNDS = 2


def main() -> None:
    state = State.load()
    recover(state)                      # 재시작 시 라벨·state 불일치 정리
    with Codex() as codex:
        while True:
            if gh.is_paused():          # agent:pause 라벨
                sleep(POLL_SECONDS); continue
            if state.current:
                watch_pr(codex, state)  # 6절 ⑨
            elif issue := gh.next_ready_issue():
                process_issue(codex, state, issue)
            sleep(POLL_SECONDS)


def process_issue(codex, state, issue) -> None:
    gh.set_label(issue, "agent:working")
    wt = workspace.create(issue)                       # worktree + 의존성 설치
    try:
        thread_id, report = agent.implement(codex, wt.path, issue.as_prompt())
        if report["status"] != "done":
            gh.park(issue, report)                     # needs-info / blocked + 댓글
            workspace.remove(wt)
            return
        report = verify_review_cycle(codex, wt, issue, thread_id, report)
        guards.check(wt, issue)                        # 금지 경로·테스트 약화·크기
        workspace.commit_and_push(wt, issue, report)
        pr = gh.create_pr(wt, issue, report)
        gh.set_label(issue, "agent:pr-open")
        state.start(issue, pr, wt, thread_id)
    except LoopStop as exc:                            # 상한 초과·가드 위반·SDK 오류
        gh.block(issue, str(exc))
        workspace.remove(wt)


def verify_review_cycle(codex, wt, issue, thread_id, report) -> dict:
    for _ in range(MAX_REVIEW_ROUNDS + 1):
        for attempt in range(1, MAX_VERIFY_ATTEMPTS + 1):
            outcome = run_verify(wt.path)              # scripts/verify.ps1
            if outcome.passed:
                break
            if attempt == MAX_VERIFY_ATTEMPTS:
                raise LoopStop(f"verify {MAX_VERIFY_ATTEMPTS}회 실패\n{outcome.tail}")
            report = agent.fix(codex, wt.path, thread_id, outcome.tail)
        findings = agent.review(codex, wt.path, issue.as_prompt(), wt.diff())
        if not findings["blocking"]:
            report["advisory"] = findings["advisory"]
            return report
        report = agent.fix(codex, wt.path, thread_id, format_findings(findings["blocking"]))
    raise LoopStop("리뷰 차단 항목 해소 실패")
```

### 7.3 GitHub 조작 (`github.py`)

인증이 끝난 `gh` CLI를 `subprocess`로 호출하고 `--json` 출력을 파싱한다. 예:

```text
gh issue list --label agent:ready --state open --author ddarahakit2024 --json number,title,body,labels
gh issue edit N --add-label agent:working --remove-label agent:ready
gh issue comment N --body-file comment.md
gh pr create --base main --head <branch> --title <t> --body-file body.md
gh pr view <pr> --json state,mergedAt,reviews,comments,statusCheckRollup
```

---

## 8. 안전장치

| 위험 | 장치 |
| --- | --- |
| 잘못된 코드가 main에 들어감 | 머지는 사람만, 브랜치 보호 + CI 필수 |
| 프롬프트 인젝션(타인의 이슈·댓글) | 소유자 작성 이슈·댓글만 처리, `agent:ready`는 사람이 붙임 |
| Codex가 GitHub·비밀값에 접근 | Codex 프로세스 환경에서 `GH_TOKEN`·`GITHUB_TOKEN`·결제 키 제거, worktree에 `.env` 없음, 샌드박스 `workspace_write`(네트워크 기본 차단) |
| 무한 반복·비용 폭주 | verify 3회·리뷰 2회·PR 피드백 2회 상한, `TurnResult.usage`를 이슈별로 합산해 상한 초과 시 blocked, 턴 시간 상한 |
| 테스트 약화·하네스 자기 수정 | 1차: `PreToolUse` 훅이 보호 경로 수정을 시도 시점에 거부(02 문서 4.11). 2차: diff 가드(6절 ⑥) — 훅이 비활성이어도 동작 |
| main에서 직접 작업 | 루프는 항상 이슈 브랜치 worktree를 만든다. 대화형 세션은 `PreToolUse` 훅이 main 수정을 거부 |
| 루프가 서버를 띄우고 방치 | verify는 서버를 띄우지 않음. E2E는 전용 포트에서 자기 서버를 띄우고 종료(02 문서 4.6). 이슈 처리 후 worktree 내 잔여 프로세스 확인 |
| PC 재부팅·루프 중단 | 라벨이 상태의 원본, `state.json`으로 현재 이슈·PR·thread_id 복구. `agent:working`인데 state가 없으면 worktree 정리 후 `agent:ready`로 되돌림 |
| 긴급 정지 | `agent:pause` 라벨, 또는 루프 프로세스 종료(진행 중 이슈는 재시작 시 복구 규칙 적용) |
| 운영 DB 손상 | 테스트 app.db 가드(H-4), worktree에는 `app.db` 없음(gitignore) |

---

## 9. 운영 방법

- 실행: 사용자 PC에서 `python -m scripts.agent_loop` (사용자가 직접 실행하는 장기 프로세스). 로그는 `.agent-loop/logs/`.
- 하루 루틴: 아침에 `agent:pr-open` PR들을 검토·머지 → 루프가 다음 이슈를 이어서 처리. 다음에 할 이슈들에 `agent:ready`를 붙여 둔다.
- `agent:blocked`·`agent:needs-info` 이슈는 원인을 보고 이슈 본문을 보강하거나, 반복되는 원인이면 03 문서의 **개선 루프**로 하네스를 고친다.
- 처음 몇 건은 작은 이슈(H 이후의 B-3 같은 프런트 정리, 단순 API)로 루프 자체를 검증한 뒤 `risk:high` 이슈를 넣는다.

### 나중에 고려할 확장

- **이벤트 기반 전환**: 폴링 대신 GitHub Actions(`issues: labeled`, `pull_request: closed`)에서 루프를 깨우는 방식. 다만 Actions 러너에서 Codex를 돌리려면 인증·비용·비밀값 관리가 추가로 필요하므로, 로컬 폴링으로 충분히 안정화한 뒤 검토한다.
- **병렬 처리**: 서로 다른 폴더만 건드리는 이슈 2개를 동시에 처리. 충돌·리뷰 부담이 커지므로 단일 강사 프로젝트 규모에서는 순차 처리를 기본으로 유지한다.

## 참고

- Codex SDK 문서: https://developers.openai.com/codex/sdk
- Python SDK 저장소: https://github.com/openai/codex/tree/main/sdk/python (API 레퍼런스: `sdk/python/docs/api-reference.md`)
