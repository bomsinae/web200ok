# 웹페이지 모니터링 시스템

## 모니터링 시나리오
1. 사용자는 URL, 모니터링 최대시간(초), 응답 키워드를 넣는다.
2. 시스템은 지정한 시간(예:5분)마다 사용자가 입력한 URL을 모니터링 한다.
3. 정상적으로 응답 받았을 때의 리턴코드와 응답시간을 기록한다.
4. 사용자가 키워드를 입력했으면 응답내용에 키워드가 있는지 확인한다.
5. 사용자가 키워드를 비웠으면 응답내용에서 키워드를 확인하지 않는다.
6. 응답코드가 200대 코드가 아니거나, 키워드를 발견하지 못했거나, 모니터링 최대시간에 도달하면 기록한다.
7. 응답코드가 200대 코드가 아니거나, 키워드를 발견하지 못했거나, 모니터링 최대시간에 도달하면 알람을 보낸다.

## 시스템 구조
1. 프레임워크는 django를 사용한다.
2. 사용자와 url 정보는 dblite3를 사용한다.
3. 모니터링 기록은 dblite3를 사용한다.

## 기능 목록
- 웹페이지 상태 모니터링 (응답 코드, 응답 시간)
- 키워드 기반 컨텐츠 모니터링
- 모니터링 실패 시 팀즈 훅으로 알림
- 모니터링 이력 조회 및 다운로드

## 기술 스택
- **백엔드**: Django 4.x
- **데이터베이스**: SQLite3
- **비동기 작업 처리**: Celery
- **알림 서비스**: MS Teams
- **프론트엔드**: HTML, CSS, JavaScript (Bootstrap 5)
- **배포**: Docker, Nginx

## 설치 방법
```bash
# 저장소 클론
git clone https://github.com/bomsinae/web200ok.git
cd web200ok

# 가상환경 생성 및 활성화
python -m venv .venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# redis 설치
sudo apt install redis redis-server

# .env 파일 만들기
vi .env
----------
DEBUG=True
ALLOWED_HOSTS=monitor.bgfoo.com, 127.0.0.1

CSRF_TRUSTED_ORIGINS=https://monitor.bgfoo.com

TEAMS_WEBHOOK=*******

USER_AGENT="WebMonitor"
ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
ACCEPT_LANGUAGE="ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
CONNECTION="keep-alive"
UPGRADE_INSECURE_REQUESTS="1"
------------------

# logs 디렉토리 만들기
mkdir logs

# 데이터베이스 마이그레이션
python manage.py migrate

# 최초 사용자 생성(id는 이메일로 생성한다.)
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver
```

## 사용 방법
1. 웹 인터페이스 접속: http://localhost:8000
2. 회원가입 후 로그인
3. '새 모니터링 추가' 버튼 클릭
4. URL, 모니터링 최대시간(초), 응답 키워드 입력 후 저장
5. 대시보드에서 모니터링 상태 확인
