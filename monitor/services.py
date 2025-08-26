import html
import asyncio
from asgiref.sync import sync_to_async
import httpx
import logging
import time
import re
from django.contrib.auth.models import User
from django.conf import settings
from .models import Http, HttpResult, HttpLastResult
from telegram import Bot
from datetime import timedelta

logger = logging.getLogger(__name__)


class HttpMonitoringService:
    """웹사이트 모니터링 작업을 처리하는 서비스 클래스"""

    @staticmethod
    def check_http(http):
        """단일 웹사이트 모니터링 체크 및 결과 저장 (1회만 시도)"""
        # 1차 시도
        start_time = time.time()
        status = 'success'
        response_code = None
        error_message = ''
        try:
            headers = {
                'User-Agent': settings.USER_AGENT,
                'Accept': settings.ACCEPT,
                'Accept-Language': settings.ACCEPT_LANGUAGE,
                'Connection': settings.CONNECTION,
                'Upgrade-Insecure-Requests': settings.UPGRADE_INSECURE_REQUESTS,
            }
            with httpx.Client(timeout=http.max_response_time, headers=headers) as client:
                response = client.get(http.url)
            response_code = response.status_code
            body_text = response.text
            response_time = time.time() - start_time
            if response_code >= 400:
                status = 'http_error'
                # HTML 태그 제거 후 빈 줄도 제거
                text_only = re.sub('<[^<]+?>', '', response.text)
                # 빈 줄 제거
                text_only = '\n'.join(
                    [line for line in text_only.splitlines() if line.strip()])
                error_message = f"HTTP Error: {text_only.strip() if text_only else response_code}"
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

        # 실패 시 1회 재시도
        if status != 'success':
            time.sleep(5)
            try:
                start_time = time.time()
                with httpx.Client(timeout=http.max_response_time, headers=headers) as client:
                    response = client.get(http.url)
                response_code = response.status_code
                body_text = response.text
                response_time = time.time() - start_time
                if response_code >= 400:
                    status = 'http_error'
                    # HTML 태그 제거 후 빈 줄도 제거
                    text_only = re.sub('<[^<]+?>', '', response.text)
                    # 빈 줄 제거
                    text_only = '\n'.join(
                        [line for line in text_only.splitlines() if line.strip()])
                    error_message = f"HTTP Error: {text_only.strip() if text_only else response_code}"
                elif http.keyword and http.keyword not in response.text:
                    status = 'keyword_not_found'
                    error_message = f"키워드 '{http.keyword}'를 찾을 수 없습니다"
                else:
                    status = 'success'
                    error_message = ''
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

        result = HttpResult.objects.create(
            account=http.account,
            http=http,
            status=status,
            response_code=response_code,
            response_time=response_time,
            error_message=error_message
        )
        HttpLastResult.objects.update_or_create(
            http=http,
            defaults={
                'status': status,
                'response_code': response_code,
                'response_time': response_time,
                'error_message': error_message,
                'checked_at': result.checked_at,
            }
        )
        # 모든 모니터링 결과를 로그로 남김
        logger.info(
            f"모니터링: {http.label} ({http.url}) - 상태: {status}, 응답코드: {response_code}, 응답시간: {response_time:.2f}s")
        return result
