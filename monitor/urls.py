from django.urls import path

from .views import http_list, http_create, http_update, http_delete
from .views import monitor_result


app_name = 'monitor'

urlpatterns = [
    path('http_list/', http_list, name='http_list'),
    path('http_create/', http_create, name='http_create'),
    path('http_update/<int:http_id>/', http_update, name='http_update'),
    path('http_delete/<int:http_id>/', http_delete, name='http_delete'),

    path('monitor_result/', monitor_result, name='monitor_result'),
    path('monitor_result/<int:http_id>/', monitor_result, name='monitor_result')
]
