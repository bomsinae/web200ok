from django.db import models
from cf_account.models import Account

# Create your models here.


class Http(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name='account_http')
    url = models.URLField(max_length=255, unique=True)
    label = models.CharField(max_length=255)
    keyword = models.CharField(max_length=255, blank=True)
    max_response_time = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = "HTTP 모니터링"
        verbose_name_plural = "HTTP 모니터링"


class HttpResult(models.Model):
    """모니터링 결과를 저장하는 모델"""
    STATUS_CHOICES = (
        ('success', '성공'),
        ('timeout', '시간 초과'),
        ('keyword_not_found', '키워드 없음'),
        ('http_error', 'HTTP 오류'),
        ('connection_error', '연결 오류'),
        ('other_error', '기타 오류'),
    )

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name='account_http_result')
    http = models.ForeignKey(
        Http, on_delete=models.CASCADE, related_name='http_result')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.http.label} - {self.status} at {self.checked_at}"

    class Meta:
        verbose_name = "HTTP 모니터링 결과"
        verbose_name_plural = "HTTP 모니터링 결과"
        indexes = [
            # Window Function 최적화: http별 최신 결과 조회
            models.Index(fields=['http', '-checked_at'],
                         name='http_checked_desc_idx'),
            # 전체 최신 결과 정렬 최적화
            models.Index(fields=['-checked_at'], name='checked_at_desc_idx'),
            # 상태별 필터링 최적화
            models.Index(fields=['status'], name='status_idx'),
            # 복합 쿼리 최적화 (status 제외 후 정렬)
            models.Index(fields=['status', '-checked_at'],
                         name='status_checked_idx'),
        ]
