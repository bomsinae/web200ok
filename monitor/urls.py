from django.urls import path

from .views import http_list
from .views import monitor_result
from .views import register_monitoring_url


app_name = 'monitor'

urlpatterns = [
    path('http_list/', http_list, name='http_list'),

    path('monitor_result/', monitor_result, name='monitor_result'),
    path('monitor_result/<int:http_id>/',
         monitor_result, name='monitor_result'),

    path('register_monitoring_url/', register_monitoring_url,
         name='register_monitoring_url')
]
