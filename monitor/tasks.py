from celery import shared_task, group
from .services import HttpMonitoringService
from .models import Http
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_website(http_id):
    """단일 웹사이트를 모니터링하는 작업"""
    try:
        http = Http.objects.get(id=http_id)
        result = HttpMonitoringService.check_http(http)
        logger.info(f"웹사이트 '{http.label}' 모니터링 완료: {result.status}")
        return {
            'id': http.id,
            'label': http.label,
            'status': result.status,
        }
    except Http.DoesNotExist:
        logger.error(f"ID {http_id}인 웹사이트를 찾을 수 없습니다.")
        return {'error': f"웹사이트 ID {http_id}를 찾을 수 없음"}
    except Exception as e:
        logger.error(f"웹사이트 ID {http_id} 모니터링 중 오류 발생: {str(e)}")
        return {'error': str(e)}


@shared_task
def check_all_websites():
    """모든 활성화된 웹사이트를 모니터링하는 주기적 작업 (병렬 처리)"""
    try:
        # 모든 활성화된 모니터링 대상 가져오기
        http_ids = list(Http.objects.filter(
            is_active=True, account__is_monitor=True).values_list('id', flat=True))

        if not http_ids:
            logger.info("활성화된 모니터링 대상이 없습니다.")
            return 0

        # 각 웹사이트별로 개별 작업 생성하여 병렬 처리
        job = group(check_website.s(http_id) for http_id in http_ids)
        result = job.apply_async()

        logger.info(f"{len(http_ids)}개의 웹사이트 모니터링 작업을 병렬로 시작했습니다.")
        return len(http_ids)
    except Exception as e:
        logger.error(f"웹사이트 모니터링 일괄 작업 시작 중 오류 발생: {str(e)}")
        raise
