from celery import shared_task, group, chord
from .services import HttpMonitoringService
from .models import Http, HttpResult
import logging
import asyncio
import httpx
from django.conf import settings
import json

logger = logging.getLogger(__name__)


@shared_task
def check_http_task(http_id):
    """단일 URL 모니터링 (병렬용)"""
    try:
        http = Http.objects.get(id=http_id)
        result = HttpMonitoringService.check_http(http)
        return {
            'id': http.id,
            'account_name': http.account.name,
            'label': http.label,
            'url': http.url,
            'status': result.status,  # HttpResult의 status 그대로 반환
            'response_code': result.response_code,
            'response_time': result.response_time,
        }
    except Exception as e:
        logger.error(f"check_http_task 오류: {str(e)}")
        return {'id': http_id, 'status': 'other_error', 'error': str(e)}


async def send_teams_webhook(messages):
    """팀즈 웹훅으로 메시지 전송"""
    if not settings.TEAMS_WEBHOOK:
        logger.error("TEAMS_WEBHOOK이 설정되지 않았습니다.")
        return

    try:
        async with httpx.AsyncClient() as client:
            for message in messages:
                # 팀즈 메시지 카드 형식으로 변환
                teams_message = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "d63333",
                    "summary": "웹사이트 모니터링 알림",
                    "sections": [{
                        "activityTitle": "⚠️ 웹사이트 모니터링 알림",
                        "text": message.replace('\n', '<br>'),
                        "markdown": True
                    }]
                }

                response = await client.post(
                    settings.TEAMS_WEBHOOK,
                    json=teams_message,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )

                if response.status_code != 200:
                    logger.error(
                        f"팀즈 웹훅 전송 실패: {response.status_code}, {response.text}")
                else:
                    logger.info("팀즈 웹훅 메시지 전송 성공")

    except Exception as e:
        logger.error(f"팀즈 웹훅 전송 중 오류: {str(e)}")


@shared_task
def process_monitoring_results(results):
    """모든 병렬 모니터링 결과를 집계하고, 비정상 상태 발견시 팀즈 웹훅으로 알림"""
    display_map = dict(HttpResult._meta.get_field('status').choices)
    error_results = [r for r in results if r.get('status') != 'success']
    total = len(results)
    error_count = len(error_results)

    # 비정상 상태가 하나라도 있으면 메시지 전송
    if error_count > 0:
        messages = []
        for r in error_results:
            status_display = display_map.get(r.get('status'), r.get('status'))
            message = (
                f"⚠️ 웹사이트 모니터링 알림 ⚠️\n\n"
                f"Account: {r.get('account_name', 'N/A')}\n"
                f"라벨: {r.get('label', 'N/A')}\n"
                f"URL: {r.get('url', 'N/A')}\n"
                f"상태: {status_display}\n"
                f"응답 코드: {r.get('response_code') if r.get('response_code') else 'N/A'}\n"
                f"응답 시간: {r.get('response_time'):.2f}초"
            )
            messages.append(message)
        asyncio.run(send_teams_webhook(messages))

    logger.info(
        f"process_monitoring_results 병렬 실행 완료: {len(results)}건 처리, 오류 {error_count}건")
    return total


@shared_task
def run_monitoring_all():
    """모든 활성화된 모니터링을 병렬로 실행하고, 비정상 상태 발견시 팀즈 웹훅으로 알림 (chord 사용)
    외부 네트워크 연결이 안되면 전체 모니터링을 중단한다."""
    # 외부 네트워크 체크 (예: google.com)
    try:
        httpx.get("https://www.google.com", timeout=5)
    except Exception:
        logger.error(
            "[모니터링 중단] 모니터링 서버의 외부 네트워크 연결에 문제가 있습니다. 전체 모니터링을 중단합니다.")
        return 0
    http_ids = list(Http.objects.filter(
        is_active=True, account__is_monitor=True).values_list('id', flat=True))
    if not http_ids:
        logger.info("활성화된 모니터링 대상이 없습니다.")
        return 0
    job = group(check_http_task.s(http_id) for http_id in http_ids)
    callback = process_monitoring_results.s()
    chord(job)(callback)
    logger.info(f"run_monitoring_all 병렬 작업 시작({len(http_ids)}건)")
    return len(http_ids)
