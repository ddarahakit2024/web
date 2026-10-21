# GitHub Actions 배포 설정

`main` 브랜치에 push(또는 PR 머지)되면 변경된 경로에 따라 워크플로우가 실행됩니다. Actions 탭에서 `workflow_dispatch`로 수동 실행도 가능합니다.

| 변경 경로 | 워크플로우 | 동작 |
| --- | --- | --- |
| `frontend/**` | `deploy-frontend.yml` | Vue 빌드 → SSH로 업로드 → `C:\nginx-1.30.5\html`에 반영 |
| `app/**`, `requirements.txt` | `deploy-backend.yml` | SSH로 업로드 → 기존 Uvicorn 종료 → 코드 교체 → 의존성 설치 → Uvicorn 재시작 |

서버에서 실제로 실행되는 작업은 `scripts/deploy/deploy-frontend.ps1`, `scripts/deploy/deploy-backend.ps1`에 있습니다.

## GitHub 저장소 시크릿

**Settings → Secrets and variables → Actions → Repository secrets**

| Secret 이름 | 값 |
| --- | --- |
| `DEPLOY_FRONTEND_HOST` | 프론트엔드 서버 SSH 주소 (`222.112.208.68`) |
| `DEPLOY_FRONTEND_PORT` | 프론트엔드 서버 SSH 포트 (`9000`) |
| `DEPLOY_FRONTEND_USER` | 프론트엔드 서버 SSH 계정 |
| `DEPLOY_FRONTEND_PASSWORD` | 프론트엔드 서버 SSH 비밀번호 |
| `DEPLOY_BACKEND_HOST` | 백엔드 서버 SSH 주소 (`222.112.208.68`) |
| `DEPLOY_BACKEND_PORT` | 백엔드 서버 SSH 포트 (`9100`) |
| `DEPLOY_BACKEND_USER` | 백엔드 서버 SSH 계정 |
| `DEPLOY_BACKEND_PASSWORD` | 백엔드 서버 SSH 비밀번호 |

## 서버 경로 설정

경로와 Uvicorn 포트는 각 워크플로우 상단의 `env`에서 바꿉니다.

- 프론트엔드: `HTML_DIR`(Nginx html 폴더), `STAGING_DIR`(업로드 임시 폴더)
- 백엔드: `BACKEND_DIR`(실행 폴더, 기본 `C:\backend`), `STAGING_DIR`, `BACKEND_PORT`(Uvicorn 포트, 기본 `443`)

## 서버 준비 (Windows)

공통: OpenSSH Server, Windows 기본 `tar.exe`(Windows 10 1803+), PowerShell 5.1 이상.

프론트엔드 서버
- Nginx가 `C:\nginx-1.30.5`에서 실행 중이어야 합니다. 정적 파일만 교체하므로 Nginx 재시작은 하지 않습니다.
- SPA 라우팅을 위해 Nginx 설정에 `try_files $uri $uri/ /index.html;`가 필요합니다.
- 배포 시 html 폴더는 빌드 결과와 동일하게 맞춰지며(`50x.html` 제외) 이전 파일은 삭제됩니다.

백엔드 서버
- `python`이 PATH에 있어야 합니다. 첫 배포 시 `BACKEND_DIR\.venv`를 생성합니다.
- 운영용 `.env`(KAKAO_*, PORTONE_*, JWT_SECRET_KEY, DATABASE_URL), `app.db`, `certs\certificate.crt`, `certs\private.key`는 `BACKEND_DIR`에 직접 두며 배포 시 덮어쓰지 않습니다. 인증서가 있으면 HTTPS로 실행합니다.
- 서버는 `BACKEND_DIR\backend.pid`, 로그는 `BACKEND_DIR\backend.log`에 기록됩니다.
- 기존 서버는 PID 파일과 `BACKEND_PORT`를 점유한 프로세스를 기준으로 종료합니다.
- `https://api.mlops.kro.kr` 요청이 백엔드 서버의 `BACKEND_PORT`(443)로 전달되어야 합니다.
