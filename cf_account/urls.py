from django.urls import path
from .views import AccountListView, AccountCreateView, AccountUpdateView, AccountDeleteView
from monitor.views import http_list, http_create, http_update, http_delete

app_name = 'cf_account'

urlpatterns = [
    # Account
    path('', AccountListView.as_view(), name='account'),
    path('account/', AccountListView.as_view(), name='account'),
    path('account_create/', AccountCreateView.as_view(), name='account_create'),
    path('acount_update/<int:pk>',
         AccountUpdateView.as_view(), name='account_update'),
    path('account_delete/<int:pk>',
         AccountDeleteView.as_view(), name='account_delete'),

    path('http_list/<int:account_id>/', http_list, name='account_http_list'),
    path('http_create/<int:account_id>/',
         http_create, name='account_http_create'),
    path('http_update/<int:http_id>/', http_update, name='account_http_update'),
    path('http_delete/<int:http_id>/',
         http_delete, name='account_http_delete'),
]
