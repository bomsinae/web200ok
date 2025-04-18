import os
from celery import Celery

# Django 설정 모듈을 환경 변수로 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('web200ok')

# 문자열로 전달된 설정을 사용하도록 Celery 구성 ('celery'로 시작하는 설정)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 등록된 Django 앱 설정에서 tasks.py 모듈을 자동으로 로드
app.autodiscover_tasks()
