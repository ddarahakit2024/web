import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".codex" / "hooks"))
import guard  # noqa: E402


def patch(path):
    return {"input": f"*** Begin Patch\n*** Update File: {path}\n@@\n-a\n+b\n*** End Patch"}


def shell(command):
    return {"command": command}


@pytest.mark.parametrize(
    "path",
    ["app.db", ".github/workflows/ci.yml", ".codex/hooks.json", "scripts/agent_loop.py",
     "C:/work/ai_backend2/.codex/hooks/guard.py"],  # fmt: skip
)
def test_patch_to_protected_path_is_denied(path):
    assert "보호된 경로" in guard.evaluate("apply_patch", patch(path))


@pytest.mark.parametrize("path", [".env", "frontend/.env.local"])
def test_patch_to_env_is_denied(path):
    assert guard.evaluate("apply_patch", patch(path)) == guard.MSG_SECRET


@pytest.mark.parametrize("path", ["app/main.py", "tests/test_x.py", ".env.example", "docs/a.md"])
def test_patch_to_normal_path_is_allowed(path):
    assert guard.evaluate("apply_patch", patch(path)) is None


@pytest.mark.parametrize("command", ["cat .env", "Get-Content frontend/.env.local", "type .env"])
def test_reading_env_is_denied(command):
    assert guard.evaluate("Bash", shell(command)) == guard.MSG_SECRET


@pytest.mark.parametrize(
    "command",
    ["git push origin HEAD", "git reset --hard HEAD~1", "rm -f app.db", "Remove-Item app.db",
     "alembic downgrade -1"],  # fmt: skip
)
def test_dangerous_commands_are_denied(command):
    assert guard.evaluate("Bash", shell(command)) == guard.MSG_DANGEROUS


@pytest.mark.parametrize(
    "command",
    ["uvicorn app.main:app --reload", "npm run dev", "npx vite", "python main.py", "fastapi dev"],
)
def test_dev_server_is_denied(command):
    assert guard.evaluate("Bash", shell(command)) == guard.MSG_DEV_SERVER


def test_shell_write_to_protected_path_is_denied():
    assert "보호된 경로" in guard.evaluate("Bash", shell("echo x > .codex/hooks.json"))


@pytest.mark.parametrize(
    "command",
    ["git status", "cat .env.example", "python -m pytest -q 2>&1", "npm run build",
     "powershell -File scripts/verify.ps1", "cat .github/workflows/verify.yml",
     "python -c \"import os; print(os.environ.get('X'))\""],  # fmt: skip
)
def test_normal_commands_are_allowed(command):
    assert guard.evaluate("Bash", shell(command)) is None


def test_list_form_command_is_supported():
    assert guard.evaluate("shell", {"command": ["bash", "-lc", "git push"]}) == guard.MSG_DANGEROUS
