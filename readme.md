# 웹페이지 모니터링 시스템

## 모니터링 시나리오
1. 사용자는 URL, 모니터링 최대시간(초), 응답 키워드를 넣는다.
2. 시스템은 5분마다 사용자가 입력한 URL을 모니터링 한다.
3. 정상적으로 응답 받았을 때의 리턴코드와 응답시간을 기록한다.
4. 사용자가 키워드를 입력했으면 응답내용에 키워드가 있는지 확인한다.
5. 사용자가 키워드를 비웠으면 응답내용에서 키워드를 확인하지 않는다.
6. 응답코드가 200대 코드가 아니거나, 키워드를 발견하지 못했거나, 모니터링 최대시간에 도달하면 기록한다.
7. 응답코드가 200대 코드가 아니거나, 키워드를 발견하지 못했거나, 모니터링 최대시간에 도달하면  사용자의 텔레그램으로 알람을 보낸다.


## 시스템 구조
1. 프레임워크는 django를 사용한다.
2. 사용자와 url 정보는 dblite3를 사용한다.
3. 모니터링 기록은 dblite3를 사용한다.

## 기능 목록
- 웹페이지 상태 모니터링 (응답 코드, 응답 시간)
- 키워드 기반 컨텐츠 모니터링
- 모니터링 실패 시 텔레그램 알림
- 응답 시간 통계 및 그래프 제공
- 모니터링 이력 조회 및 다운로드
- 사용자별 모니터링 대시보드

## 기술 스택
- **백엔드**: Django 4.x
- **데이터베이스**: SQLite3
- **비동기 작업 처리**: Celery
- **알림 서비스**: Telegram Bot API
- **프론트엔드**: HTML, CSS, JavaScript (Bootstrap 5)
- **배포**: Docker, Nginx

## 설치 방법
```bash
# 저장소 클론
git clone https://github.com/yourusername/web200ok.git
cd web200ok

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
```

## 환경 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 설정을 추가하세요:

```
SECRET_KEY=your_django_secret_key
DEBUG=True
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## 사용 방법
1. 웹 인터페이스 접속: http://localhost:8000
2. 회원가입 후 로그인
3. '새 모니터링 추가' 버튼 클릭
4. URL, 모니터링 최대시간(초), 응답 키워드 입력 후 저장
5. 대시보드에서 모니터링 상태 확인

## 개발 로드맵
- [x] 기본 모니터링 기능 구현
- [x] 텔레그램 알림 연동
- [ ] 사용자 대시보드 개선
- [ ] 응답 시간 통계 그래프 추가
- [ ] 이메일 알림 기능 추가
- [ ] 모바일 앱 개발
- [ ] API 서비스 제공

## 기여 방법
1. 이 저장소를 포크합니다.
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 라이센스
MIT 라이센스

## 연락처
- 이메일: your.email@example.com
- 이슈 트래커: https://github.com/yourusername/web200ok/issues
