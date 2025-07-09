from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0002_httpresult_monitor_htt_http_id_4b5008_idx_and_more'),
    ]

    operations = [
        # HttpResult 테이블에 성능 최적화를 위한 복합 인덱스 추가
        migrations.RunSQL(
            "CREATE INDEX monitor_httpresult_http_checked_status_idx ON monitor_httpresult (http_id, checked_at DESC, status);",
            "DROP INDEX monitor_httpresult_http_checked_status_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX monitor_httpresult_checked_at_desc_idx ON monitor_httpresult (checked_at DESC);",
            "DROP INDEX monitor_httpresult_checked_at_desc_idx;"
        ),
    ]
