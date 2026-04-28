# Web200ok 인수인계 문서

작성일: 2026-04-28  
프로젝트 위치: `/home/ubuntu/Projects/web200ok`

## 1. 서비스 개요

Web200ok는 등록된 URL을 주기적으로 호출해 HTTP 상태, 응답 시간, 응답 본문 키워드 포함 여부를 확인하는 Django 기반 모니터링 시스템이다.

주요 기능은 다음과 같다.

- Account 단위 URL 모니터링 대상 관리
- 1분 주기 전체 모니터링 실행
- HTTP 오류, 타임아웃, 키워드 미발견, 연결 오류 탐지
- 비정상 상태 발생 시 Microsoft Teams 및 Telegram 알림 발송
- 최근 상태 대시보드, 전체 결과 목록, 비정상 목록 조회
- URL 목록과 모니터링 결과 Excel 다운로드
- 외부 API를 통한 모니터링 URL 등록/삭제

## 2. 기술 스택

- Python, Django 5.1.8
- SQLite3
- Celery 5.5.1
- Redis
- Gunicorn
- Nginx
- Bootstrap 기반 Django template
- httpx, openpyxl, python-dotenv, python-telegram-bot

의존성 파일은 `src/requirements.txt`에 있다. README에는 `requirements.txt`라고 적혀 있지만 현재 저장소 기준 실제 파일은 `src/requirements.txt`이다.

## 3. 디렉터리 구조

```text
config/          Django project 설정, URL, WSGI/ASGI, Celery 설정
common/          메인 대시보드, 로그인/회원가입, 사용자 관리
cf_account/      Account CRUD
monitor/         URL 모니터링 모델, 화면, Celery task, 서비스 로직
templates/       공통 base/sidebar template
static/          CSS, favicon, 알림 사운드 파일
src/             systemd, nginx, logrotate, requirements 배포 파일
logs/            Django/Gunicorn 로그 출력 디렉터리
manage.py        Django 관리 명령 진입점
readme.md        기존 설치/사용 안내
```

## 4. 핵심 데이터 모델

### `cf_account.Account`

Cloudflare account 또는 운영상 그룹을 표현한다.

- `name`: 고유 account 이름
- `is_monitor`: 이 account의 URL을 모니터링할지 여부
- `regdate`: 생성 일시

### `monitor.Http`

실제 모니터링 대상 URL이다.

- `account`: Account FK
- `url`: 모니터링 URL, 전역 unique
- `label`: 화면 표시명
- `keyword`: 응답 본문에서 찾을 선택 키워드
- `max_response_time`: httpx timeout 값, 초 단위
- `is_active`: URL 단위 모니터링 활성 여부
- `sort_order`: 목록 드래그 정렬 순서

### `monitor.HttpResult`

매 체크마다 생성되는 이력 테이블이다.

상태값:

- `success`
- `timeout`
- `keyword_not_found`
- `http_error`
- `connection_error`
- `other_error`

인덱스는 `http, -checked_at`, `status` 중심으로 잡혀 있다.

### `monitor.HttpLastResult`

URL별 마지막 체크 결과를 저장하는 OneToOne 테이블이다. 메인 대시보드와 URL 목록의 최근 상태 표시에 사용된다. 전체 이력에서 매번 최신 행을 찾지 않기 위한 캐시성 테이블이다.

## 5. 주요 실행 흐름

### 주기 모니터링

1. `config/settings.py`의 `CELERY_BEAT_SCHEDULE`이 매분 `monitor.tasks.run_monitoring_all`을 실행한다.
2. `run_monitoring_all`은 먼저 `https://www.google.com`으로 외부 네트워크 연결을 확인한다.
3. 연결이 정상이면 `Http.objects.filter(is_active=True, account__is_monitor=True)` 대상 id를 가져온다.
4. Celery `group`으로 `check_http_task`를 URL별 병렬 실행하고, `chord` callback으로 `process_monitoring_results`를 실행한다.
5. `check_http_task`는 DB lock 재시도 로직을 거쳐 `HttpMonitoringService.check_http`를 호출한다.
6. `check_http`는 대상 URL을 1회 호출하고, 실패 상태면 5초 대기 후 1회 재시도한다.
7. 결과는 `HttpResult`에 저장하고 `HttpLastResult`를 `update_or_create`로 갱신한다.
8. `process_monitoring_results`는 성공이 아닌 결과만 모아 Teams와 Telegram으로 알림을 보낸다.

### 상태 판단 기준

- 응답 코드가 400 이상이면 `http_error`
- `keyword`가 있고 응답 본문에 포함되지 않으면 `keyword_not_found`
- httpx timeout이면 `timeout`
- httpx request error이면 `connection_error`
- 그 외 예외는 `other_error`
- 위 조건에 걸리지 않으면 `success`

## 6. 주요 URL

루트 URL은 로그인 후 메인 대시보드이다.

```text
/                         메인 대시보드
/admin/                   Django admin
/common/login/            로그인
/common/logout/           로그아웃
/common/signup/           회원가입
/common/user/             사용자 목록
/common/abnormal_url_excel_download/

/cf_account/              Account 목록
/cf_account/account_create/
/cf_account/acount_update/<pk>
/cf_account/account_delete/<pk>
/cf_account/http_list/<account_id>/
/cf_account/http_create/<account_id>/
/cf_account/http_update/<http_id>/
/cf_account/http_delete/<http_id>/

/monitor/http_list/
/monitor/http_list_excel/
/monitor/monitor_result/
/monitor/monitor_result/<http_id>/
/monitor/monitor_result_excel/
/monitor/monitor_result_excel/<http_id>/
/monitor/update_http_order/
/monitor/register_monitoring_url/
```

주의: `cf_account/urls.py`의 account update 경로가 `acount_update/<int:pk>`로 오타 형태다. 이미 사용 중인 URL일 수 있으므로 수정 시 template 링크와 운영 북마크 영향을 같이 확인해야 한다.

## 7. 외부 등록 API

`POST /monitor/register_monitoring_url/`

요청 JSON:

```json
{
  "account_name": "account-name",
  "zone_name": "example.com",
  "cname_flag": "YES"
}
```

- `cname_flag=YES`: `https://{zone_name}`을 모니터링 URL로 등록한다.
- `cname_flag=NO`: `label=zone_name`인 URL을 삭제한다.
- 등록 전 대상 URL을 10초 timeout으로 호출하고, Cloudflare 5xx로 판단되면 등록하지 않는다.

이 API는 현재 `csrf_exempt`이고 로그인 요구가 없다. 외부 자동화 연동용으로 보이지만, 운영 노출 시 인증 토큰 또는 IP allowlist가 필요하다.

## 8. 환경 변수

`.env`를 프로젝트 루트에 둔다.

```env
DEBUG=False
ALLOWED_HOSTS=monitor.example.com,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://monitor.example.com

TEAMS_WEBHOOK=https://...
TELEGRAM_TOKEN=...

USER_AGENT=WebMonitor
ACCEPT=text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
ACCEPT_LANGUAGE=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7
CONNECTION=keep-alive
UPGRADE_INSECURE_REQUESTS=1
```

현재 `settings.py`는 `ALLOWED_HOSTS`와 `CSRF_TRUSTED_ORIGINS`가 없으면 `.split(',')`에서 예외가 난다. 신규 환경 구성 시 이 두 값은 반드시 넣어야 한다.

## 9. 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Celery까지 로컬에서 확인하려면 Redis가 떠 있어야 한다.

```bash
redis-server
celery -A config worker -l info -c 2
celery -A config beat -l info
```

## 10. 운영 구성

배포 관련 파일은 `src/`에 있다.

- `web200ok.service`: Gunicorn을 `/tmp/web200ok.sock` unix socket으로 실행
- `celery-worker.service`: `celery -A config worker -l info -c 2`
- `celery-beat.service`: `celery -A config beat -l info`
- `web200ok.conf`: Nginx reverse proxy 및 static alias
- `web200ok_log_format.conf`: Nginx log format
- `logrotate_web200ok`: `logs/server.log` daily rotate 7

운영 재시작 스크립트:

```bash
./restart_web.sh
./restart_celery.sh
```

현재 systemd 파일들은 `/home/ubuntu/Projects/web200ok` 경로와 `ubuntu` 사용자에 맞춰져 있다. 서버 계정이나 배포 경로가 바뀌면 `src/*.service`, `src/web200ok.conf`, `src/logrotate_web200ok`의 경로를 함께 바꿔야 한다.

## 11. 운영 점검 명령

```bash
systemctl status web200ok
systemctl status celery-worker
systemctl status celery-beat
systemctl status redis-server

journalctl -u web200ok -f
journalctl -u celery-worker -f
journalctl -u celery-beat -f

tail -f logs/server.log
tail -f logs/access.log
tail -f logs/error.log
tail -f /var/log/nginx/web200ok_access.log
tail -f /var/log/nginx/web200ok_error.log
```

## 12. 데이터베이스와 로그

현재 DB는 루트의 `db.sqlite3`이며 파일 크기가 큰 편이다. 모니터링 결과가 매분 누적되는 구조라 `HttpResult`가 계속 증가한다.

운영에서 주기적으로 검토할 항목:

- 오래된 `HttpResult` 보관 정책
- SQLite 파일 백업
- DB 파일 크기와 VACUUM 필요 여부
- Celery 병렬 실행 시 SQLite lock 빈도
- `logs/`와 `/var/log/nginx/` 디스크 사용량

SQLite는 간단한 운영에는 충분하지만, 대상 URL 수가 늘어나면 Celery 병렬 write와 이력 증가 때문에 PostgreSQL 전환을 고려하는 것이 좋다.

## 13. 보안 및 안정성 주의점

- `SECRET_KEY`가 `settings.py`에 하드코딩되어 있다. 운영에서는 환경 변수로 분리하는 것이 좋다.
- `.env`에는 webhook/token 등이 들어가므로 절대 커밋하지 않는다.
- `register_monitoring_url`은 인증 없는 CSRF exempt API다. 외부 노출 전 인증 장치를 추가해야 한다.
- `update_http_order`도 `csrf_exempt`다. 로그인은 필요하지만 CSRF 보호가 빠져 있다.
- 회원가입 사용자는 `is_active=False`로 생성되어 관리자 승인이 필요하다.
- Telegram chat id는 Django `User.first_name` 필드에 저장하는 방식이다.
- `send_teams_webhook`과 `send_telegram_bulk`가 모두 호출된다. Telegram token이 없는 운영이면 실패 로그가 발생할 수 있다.
- `run_monitoring_all`은 google.com 연결 실패 시 전체 모니터링을 중단한다. 폐쇄망이나 Google 접근 제한 환경이면 체크 URL 변경이 필요하다.
- README에는 Docker 배포라고 적혀 있지만 현재 저장소에는 Dockerfile이나 compose 파일이 없다.

## 14. 테스트 현황

`common/tests.py`, `cf_account/tests.py`, `monitor/tests.py` 파일은 있으나 현재 실질 테스트 코드는 확인되지 않았다. 인수 후 우선 추가하면 좋은 테스트는 다음과 같다.

- `HttpMonitoringService.check_http` 상태 판정 테스트
- 키워드 포함/미포함 테스트
- timeout/request error 처리 테스트
- `register_monitoring_url` 등록/삭제/중복/Cloudflare 5xx 처리 테스트
- `HttpLastResult` 갱신 테스트
- Excel 다운로드 응답 테스트

## 15. 인수 후 우선순위 제안

1. 운영 `.env`와 webhook/token 관리 방식 점검
2. `register_monitoring_url` 인증 추가
3. `SECRET_KEY` 환경 변수화
4. `HttpResult` 보관/삭제 정책 수립
5. SQLite lock 빈도 확인 후 PostgreSQL 전환 여부 판단
6. Telegram 미사용 환경이면 알림 분기 처리
7. README의 실제 경로와 오타 수정
8. 최소 단위 테스트 추가

