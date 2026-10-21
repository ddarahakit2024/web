# GitHub Actions 배포 설정

`main` 브랜치에 반영되면 변경된 경로에 따라 배포가 실행됩니다. `app/` 또는 `requirements.txt` 변경은 백엔드를 `9100` 포트로 재시작하고, `frontend/` 변경은 빌드한 정적 파일을 배포해 `9000` 포트로 제공합니다. PR을 `main`에 머지하면 `push` 이벤트가 발생해 해당 워크플로우가 실행됩니다.

## GitHub 저장소 설정

저장소의 **Settings → Secrets and variables → Actions → New repository secret**에서 아래 저장소 시크릿을 추가합니다.

| Secret 이름 | 값 |
| --- | --- |
| `DEPLOY_BACKEND_HOST` | 백엔드 서버 SSH 주소 |
| `DEPLOY_FRONTEND_HOST` | 프론트엔드 서버 SSH 주소 |
| `DEPLOY_BACKEND_PORT` | 백엔드 서버 SSH 포트 |
| `DEPLOY_BACKEND_USER` | 백엔드 서버 SSH 계정 |
| `DEPLOY_BACKEND_PASSWORD` | 백엔드 서버 SSH 비밀번호 |
| `DEPLOY_FRONTEND_PORT` | 프론트엔드 서버 SSH 포트 |
| `DEPLOY_FRONTEND_USER` | 프론트엔드 서버 SSH 계정 |
| `DEPLOY_FRONTEND_PASSWORD` | 프론트엔드 서버 SSH 비밀번호 |

두 `*_PORT` 값은 각 서버의 SSH 접속 포트입니다. 서비스는 별도로 백엔드 `9100`, 프론트엔드 `9000` 포트를 사용합니다. 서버 방화벽에서 서비스 포트도 허용해야 합니다.

## 서버 준비

배포 계정에 `python3`, `python3-venv`, `pip`가 설치되어 있어야 합니다. 두 서비스 파일은 계정 홈의 `~/ai_backend2` 아래에 저장되고, 배포 계정 권한으로 실행됩니다. 백엔드는 `~/ai_backend2/app.db`를 사용하도록 `DATABASE_URL`을 설정하거나 실행 경로를 확인하세요. 운영용 환경변수는 `~/ai_backend2/.env`에 두면 코드가 읽습니다. 이 파일은 GitHub에서 전송하지 않습니다.

프론트엔드는 `frontend/serve.py`로 제공되므로 `python3`가 필요합니다. 서버에서 외부로 `9000`과 `9100` 포트가 열려 있어야 합니다. 프론트엔드에서 사용할 API 주소와 백엔드 CORS 허용 주소는 별도로 실제 배포 환경에 맞게 설정해야 합니다.
