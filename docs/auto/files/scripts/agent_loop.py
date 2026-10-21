"""GitHub 이슈 -> Codex 구현 -> verify -> 리뷰 -> PR 자동 루프 (docs/05 문서의 단순화 버전).

실행: python scripts/agent_loop.py   (Ctrl+C로 종료)
- agent:ready 라벨이 붙은, 소유자가 쓴 이슈를 번호 순으로 하나씩 처리한다.
- PR이 머지되거나 닫혀야 다음 이슈로 넘어간다. 머지는 사람이 한다.
- PR에 소유자가 `/agent <요청>` 댓글을 달면 반영해서 같은 브랜치에 푸시한다.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WT_BASE = ROOT.parent / f"{ROOT.name}-wt"
STATE = ROOT / ".agent-loop" / "state.json"
OWNER = "ddarahakit2024"
MODEL = "gpt-5.6-luna"
POLL_SECONDS = 120
MAX_TRIES = 3
MAX_LINES = 800
PROTECTED = re.compile(
    r"(^|/)\.env(?!\.example$)|\.db$|^\.github/|^\.codex/|^scripts/agent_loop\.py$"
)

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"enum": ["done", "blocked"]},
        "summary": {"type": "string"},
        "commit_title": {"type": "string"},
    },
    "required": ["status", "summary", "commit_title"],
    "additionalProperties": False,
}
REVIEW_SCHEMA = {
    "type": "object",
    "properties": {"blocking": {"type": "array", "items": {"type": "string"}}},
    "required": ["blocking"],
    "additionalProperties": False,
}

IMPLEMENT_PROMPT = """아래 GitHub 이슈를 구현하라. AGENTS.md 규칙을 따른다.
- 완료 기준마다 테스트를 추가하고 powershell -File scripts/verify.ps1 을 통과시킨다.
- git 커밋·푸시, 의존성 설치, 개발 서버 실행, .env 읽기는 하지 않는다.
- 정책 결정이 필요하거나 진행할 수 없으면 status를 blocked로 두고 summary에 이유·질문을 적는다.
- commit_title은 "feat: ..." 형식 한 줄.

"""
REVIEW_PROMPT = """너는 코드를 수정하지 않는 리뷰어다. 이슈와 diff를 보고,
머지하면 확실히 문제가 되는 것(완료 기준 미충족, 권한·결제 버그, 테스트 약화)만 blocking에 적어라.
문제가 없으면 빈 배열.

"""


# ── 판단 로직 (테스트 대상) ─────────────────────────────────
def pick_issue(issues: list[dict], owner: str = OWNER) -> dict | None:
    """소유자가 쓴 이슈 중 번호가 가장 작은 것. 다른 사람의 이슈는 프롬프트 인젝션 경로라 무시한다."""
    mine = [i for i in issues if i["author"]["login"] == owner]
    return min(mine, key=lambda i: i["number"]) if mine else None


def violations(paths: list[str], changed_lines: int) -> list[str]:
    problems = [f"수정 금지 경로: {p}" for p in paths if PROTECTED.search(p)]
    if changed_lines > MAX_LINES:
        problems.append(f"변경 {changed_lines}줄이 상한 {MAX_LINES}줄을 넘음 (이슈를 나눠 주세요)")
    return problems


def new_feedback(comments: list[dict], handled: list[str], owner: str = OWNER) -> list[dict]:
    return [
        c
        for c in comments
        if c["author"]["login"] == owner
        and c["body"].strip().startswith("/agent")
        and c["id"] not in handled
    ]


# ── 외부 명령 ──────────────────────────────────────────────
def run(args: list, cwd: Path = ROOT, stdin: str | None = None, check: bool = True) -> str:
    r = subprocess.run(
        [str(a) for a in args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args[:3]))} 실패: {r.stderr.strip()[-1500:]}")
    return r.stdout


def gh(*args, stdin: str | None = None) -> str:
    return run(["gh", *args], stdin=stdin)


def git(cwd: Path, *args, check: bool = True) -> str:
    return run(["git", *args], cwd=cwd, check=check)


def load_state() -> dict | None:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None


def save_state(state: dict | None) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def set_label(number: int, add: str, remove: str) -> None:
    gh("issue", "edit", number, "--add-label", add, "--remove-label", remove)


def remove_worktree(wt: Path, branch: str) -> None:
    git(ROOT, "worktree", "remove", "--force", wt, check=False)
    git(ROOT, "worktree", "prune", check=False)
    git(ROOT, "branch", "-D", branch, check=False)


def verify(wt: Path) -> tuple[bool, str]:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/verify.ps1"],
        cwd=wt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "VERIFY_PYTHON": sys.executable},
    )
    lines = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode == 0, "\n".join(lines[-50:])


def ask(codex, wt: Path, prompt: str, schema: dict, thread_id=None, read_only=False):
    """Codex 턴 1회. SDK 이름이 다르면 이 함수만 고치면 된다."""
    from openai_codex import Sandbox

    sandbox = Sandbox.read_only if read_only else Sandbox.workspace_write
    if thread_id:
        thread = codex.thread_resume(thread_id, cwd=str(wt), sandbox=sandbox)
    else:
        thread = codex.thread_start(cwd=str(wt), sandbox=sandbox, model=MODEL)
    result = thread.run(prompt, output_schema=schema)
    if result.error or not result.final_response:
        raise RuntimeError(f"Codex 턴 실패: {result.error}")
    return thread.id, json.loads(result.final_response)


# ── 처리 절차 ──────────────────────────────────────────────
def build(codex, wt: Path, task: str, prompt: str, thread_id=None):
    """지시 수행 -> verify -> 리뷰 -> 가드. 실패하면 같은 스레드에 피드백하며 최대 MAX_TRIES회."""
    for _ in range(MAX_TRIES):
        thread_id, report = ask(codex, wt, prompt, REPORT_SCHEMA, thread_id)
        if report["status"] != "done":
            raise RuntimeError(f"Codex가 멈춤: {report['summary']}")
        ok, tail = verify(wt)
        if not ok:
            prompt = f"verify가 실패했다. 고쳐라:\n{tail}"
            continue
        git(wt, "add", "-A")
        diff = git(wt, "diff", "--cached", "origin/main")
        review_prompt = f"{REVIEW_PROMPT}{task}\n\n{diff[:200_000]}"
        _, review = ask(codex, wt, review_prompt, REVIEW_SCHEMA, read_only=True)  # 새 스레드
        if review["blocking"]:
            prompt = "리뷰에서 나온 차단 항목을 고쳐라:\n- " + "\n- ".join(review["blocking"])
            continue
        paths = git(wt, "diff", "--cached", "--name-only", "origin/main").split()
        numstat = git(wt, "diff", "--cached", "--numstat", "origin/main").splitlines()
        changed = sum(int(n) for row in numstat for n in row.split("\t")[:2] if n.isdigit())
        if problems := violations(paths, changed):
            raise RuntimeError("\n".join(problems))
        return thread_id, report
    raise RuntimeError(f"{MAX_TRIES}회 시도 후에도 통과하지 못함. 마지막 피드백:\n{prompt[-2000:]}")


def start_issue(codex, issue: dict) -> None:
    n = issue["number"]
    branch, wt = f"agent/issue-{n}", WT_BASE / f"issue-{n}"
    task = f"# 이슈 #{n}: {issue['title']}\n\n{issue['body']}"
    set_label(n, "agent:working", "agent:ready")
    try:
        git(ROOT, "fetch", "origin")
        remove_worktree(wt, branch)
        git(ROOT, "worktree", "add", wt, "-b", branch, "origin/main")
        run([shutil.which("npm") or "npm", "ci"], cwd=wt / "frontend")  # Codex는 네트워크가 없다
        thread_id, report = build(codex, wt, task, IMPLEMENT_PROMPT + task)
        git(wt, "commit", "-m", f"{report['commit_title']} (#{n})", "-m", report["summary"])
        git(wt, "push", "-u", "origin", branch)
        body = f"Closes #{n}\n\n{report['summary']}\n\n수정 요청은 이 PR에 `/agent <내용>` 댓글로."
        title = report["commit_title"]
        url = gh("pr", "create", "--head", branch, "--title", title, "--body-file", "-", stdin=body)
        set_label(n, "agent:pr-open", "agent:working")
        pr = int(url.strip().rsplit("/", 1)[-1])
        save_state(
            {"issue": n, "pr": pr, "branch": branch, "worktree": str(wt),
             "thread_id": thread_id, "task": task, "handled": []}
        )
        print(f"#{n} PR 생성: {url.strip()}")
    except Exception as exc:
        set_label(n, "agent:blocked", "agent:working")
        gh("issue", "comment", n, "--body-file", "-", stdin=f"자동 처리 중단:\n```\n{exc}\n```")
        remove_worktree(wt, branch)


def watch_pr(codex, state: dict) -> None:
    wt = Path(state["worktree"])
    pr = json.loads(gh("pr", "view", state["pr"], "--json", "state,comments"))
    if pr["state"] in ("MERGED", "CLOSED"):
        print(f"#{state['issue']} PR {pr['state']} -> 다음 이슈로")
        gh("issue", "edit", state["issue"], "--remove-label", "agent:pr-open")
        remove_worktree(wt, state["branch"])
        save_state(None)
        return
    feedback = new_feedback(pr["comments"], state["handled"])
    if not feedback:
        return
    state["handled"] += [c["id"] for c in feedback]
    save_state(state)
    request = "\n".join(c["body"].strip()[len("/agent") :] for c in feedback)
    try:
        state["thread_id"], report = build(
            codex, wt, state["task"], f"PR 피드백을 반영하라:\n{request}", state["thread_id"]
        )
        save_state(state)
        git(wt, "commit", "-m", f"{report['commit_title']} (#{state['issue']})")
        git(wt, "push")
        message = f"반영했습니다.\n\n{report['summary']}"
    except Exception as exc:
        message = f"반영 실패:\n```\n{exc}\n```"
    gh("pr", "comment", state["pr"], "--body-file", "-", stdin=message)


def main() -> None:
    from openai_codex import Codex

    with Codex() as codex:
        while True:
            try:
                if state := load_state():
                    watch_pr(codex, state)
                else:
                    fields = "number,title,body,author"
                    issues = json.loads(gh("issue", "list", "--label", "agent:ready", "--json", fields))
                    if issue := pick_issue(issues):
                        start_issue(codex, issue)
            except Exception as exc:  # gh 일시 오류 등은 다음 폴링에서 재시도
                print("오류:", exc)
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
