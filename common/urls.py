from django.urls import path
from .views import signup, signup_success
from .views import UserListView, UserUpdateView, UserDeleteView
from django.contrib.auth import views as auth_views

app_name = 'common'

urlpatterns = [
    # 로그인
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('signup/success/', signup_success, name='signup_success'),
    path('user/', UserListView.as_view(), name='user'),
    path('user_update/<int:pk>', UserUpdateView.as_view(), name='user_update'),
    path('user_delete/<int:pk>', UserDeleteView.as_view(), name='user_delete'),
]
