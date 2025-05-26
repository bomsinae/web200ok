from celery import shared_task, group, chord
from .services import HttpMonitoringService
from .models import Http, HttpResult
import logging
import asyncio

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


@shared_task
def process_monitoring_results(results):
    """모든 병렬 모니터링 결과를 집계하고, 5% 이상 오류시 텔레그램 알림"""
    display_map = dict(HttpResult._meta.get_field('status').choices)
    error_results = [r for r in results if r.get('status') != 'success']
    total = len(results)
    error_count = len(error_results)
    if total > 0 and error_count / total >= 0.05:
        for r in error_results:
            try:
                status_display = display_map.get(
                    r.get('status'), r.get('status'))
                message = (
                    f"⚠️ 웹사이트 모니터링 알림 ⚠️\n\n"
                    f"Account: {r.get('account_name', 'N/A')}\n"
                    f"라벨: {r.get('label', 'N/A')}\n"
                    f"URL: {r.get('url', 'N/A')}\n"
                    f"상태: {status_display}\n"
                    f"응답 코드: {r.get('response_code') if r.get('response_code') else 'N/A'}\n"
                    f"응답 시간: {r.get('response_time'):.2f}초"
                )
                asyncio.run(HttpMonitoringService.send_telegram(message))
            except Exception as e:
                logger.error(f"텔레그램 알림 전송 중 오류: {str(e)}")
    logger.info(
        f"process_monitoring_results 병렬 실행 완료: {len(results)}건 처리, 오류 {error_count}건")
    return total


@shared_task
def run_monitoring_all():
    """모든 활성화된 모니터링을 병렬로 실행하고, 5% 이상 오류시 텔레그램 알림 (chord 사용)"""
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
