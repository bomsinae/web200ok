import html
import asyncio
from asgiref.sync import sync_to_async
import httpx
import logging
import time
from django.contrib.auth.models import User
from django.conf import settings
from .models import Http, HttpResult
from telegram import Bot
from datetime import timedelta

logger = logging.getLogger(__name__)


class HttpMonitoringService:
    """웹사이트 모니터링 작업을 처리하는 서비스 클래스"""

    @staticmethod
    def check_http(http):
        """단일 웹사이트 모니터링 체크 수행"""
        start_time = time.time()
        status = 'success'
        response_code = None
        error_message = ''

        try:
            # User-Agent 및 기타 헤더 설정
            headers = {
                'User-Agent': settings.USER_AGENT,
                'Accept': settings.ACCEPT,
                'Accept-Language': settings.ACCEPT_LANGUAGE,
                'Connection': settings.CONNECTION,
                'Upgrade-Insecure-Requests': settings.UPGRADE_INSECURE_REQUESTS,
            }
            # timeout is specified in seconds
            with httpx.Client(timeout=http.max_response_time, headers=headers) as client:
                response = client.get(http.url)
            response_code = response.status_code

            # 응답 시간 계산
            response_time = time.time() - start_time

            # 응답 코드 확인
            if not 200 <= response_code < 500:
                status = 'http_error'
                error_message = f"HTTP Error: {response.text if response.text else response_code}"

            # 키워드 확인 (설정된 경우)
            elif http.keyword and http.keyword not in response.text:
                status = 'keyword_not_found'
                error_message = f"키워드 '{http.keyword}'를 찾을 수 없습니다"

        except httpx.TimeoutException:
            response_time = http.max_response_time
            status = 'timeout'
            error_message = f"응답 시간 초과 ({http.max_response_time}초)"

        except httpx.RequestError as e:
            response_time = time.time() - start_time
            status = 'connection_error'
            error_message = f"연결 오류 발생: {str(e)}"

        except Exception as e:
            response_time = time.time() - start_time
            status = 'other_error'
            error_message = f"오류 발생: {str(e)}"

        # 결과 저장
        result = HttpResult.objects.create(
            account=http.account,
            http=http,
            status=status,
            response_code=response_code,
            response_time=response_time,
            error_message=error_message
        )

        # 알림이 필요한 경우 (오류 발생시)
        if status != 'success':
            HttpMonitoringService.send_alert(http, result)

        return result

    @staticmethod
    def send_alert(http, result):
        """알림 전송"""

        # error_message가 너무 길면 자르기 (예: 1000자 제한)
        MAX_ERROR_MSG_LEN = 1000
        error_msg = result.error_message or 'N/A'
        if len(error_msg) > MAX_ERROR_MSG_LEN:
            error_msg = error_msg[:MAX_ERROR_MSG_LEN] + '... (생략됨)'

        message = f"""⚠️ 웹사이트 모니터링 알림 ⚠️

        Account: {http.account.name}
        라벨: {http.label}
        URL: {http.url}
        상태: {result.get_status_display()}
        응답 코드: {result.response_code if result.response_code else 'N/A'}
        응답 시간: {result.response_time:.2f}초
        오류: {html.escape(error_msg)}
        """

        asyncio.run(HttpMonitoringService.send_telegram(message))

    @staticmethod
    async def send_telegram(message):
        users = await sync_to_async(list)(User.objects.exclude(first_name=''))

        for user in users:
            chat_id = user.first_name
            bot = Bot(token=settings.TELEGRAM_TOKEN)
            try:
                result = await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML"
                )
                print(result.to_dict())
                logger.info(f"텔레그램 알림이 전송되었습니다: {result.to_dict()}")
            except Exception as e:
                print(f"ERROR -> Telegram, {chat_id}, {e}")
                logger.error(f"텔레그램 알림 전송 중 오류 발생: {chat_id}, {str(e)}")

    @staticmethod
    def run_all_active_http():
        """모든 활성화된 모니터링 실행"""
        http_list = Http.objects.filter(
            is_active=True, account__is_monitor=True)
        results = []

        for http in http_list:
            try:
                result = HttpMonitoringService.check_http(http)
                results.append(result)
            except Exception as e:
                logger.error(f"모니터링 실행 중 오류 발생 ({http.label}): {str(e)}")

        return results
