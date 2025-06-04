from django.urls import path

from .views import http_list
from .views import http_list_excel
from .views import monitor_result
from .views import register_monitoring_url
from .views import monitor_result_excel


app_name = 'monitor'

urlpatterns = [
    path('http_list/', http_list, name='http_list'),
    path('http_list_excel/', http_list_excel, name='http_list_excel'),
    path('http_list_excel/<int:account_id>/',
         http_list_excel, name='http_list_excel'),

    path('monitor_result/', monitor_result, name='monitor_result'),
    path('monitor_result/<int:http_id>/',
         monitor_result, name='monitor_result'),

    path('register_monitoring_url/', register_monitoring_url,
         name='register_monitoring_url'),

    path('monitor_result_excel/', monitor_result_excel,
         name='monitor_result_excel'),
    path('monitor_result_excel/<int:http_id>/',
         monitor_result_excel, name='monitor_result_excel'),
]
