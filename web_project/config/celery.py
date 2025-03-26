from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django의 settings 모듈을 기본으로 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('web_project')

# Celery가 사용할 메시지 브로커로 Redis 사용
app.config_from_object('django.conf:settings', namespace='CELERY')

# Redis 서버 URL 설정 (EC2에서 실행 중인 Redis 서버 사용)
app.conf.broker_url = 'redis://localhost:6379/0'  # Redis 연결 (localhost에서 실행 중)

# Celery 작업을 자동으로 탐지해서 등록
app.autodiscover_tasks()

# Celery 앱 인스턴스를 반환
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))