from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, UserUpdateForm
from monitor.models import Http, HttpResult


@login_required
def main(request):
    """
    비상정적인 페이지와 꺼저있는 페이지 보여주기.
    """

    # 각 URL의 마지막 모니터링 결과를 가져오기 위한 쿼리
    from django.db.models import Max, Subquery, OuterRef

    # 각 HTTP URL별 가장 최근 체크 시간 구하기
    latest_checks = HttpResult.objects.filter(
        http=OuterRef('http')
    ).order_by('-checked_at').values('id')[:1]

    # 위에서 구한 최근 체크 결과만 가져오기
    latest_results = HttpResult.objects.filter(
        id__in=Subquery(latest_checks)
    )

    # 그 중에서 status가 'success'가 아닌 것만 필터링
    http_results = latest_results.exclude(
        status='success').order_by('-checked_at')

    # 모니터링이 꺼져 있는 URL을 가져오기
    http_off_list = Http.objects.filter(is_active=False)

    context = {
        'http_results': http_results,
        'http_off_list': http_off_list,
    }

    return render(request, 'common/main.html', context)


def signup_success(request):
    return render(request, 'registration/signup_success.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # 비밀번호 설정
            user.is_active = False  # 관리자 승인이 필요하도록 비활성화
            user.save()
            return redirect('common:signup_success')  # 성공 페이지로 리디렉션
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'common/user_list.html'


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'common/user_update.html'
    success_url = reverse_lazy('common:user')


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'common/user_confirm_delete.html'
    success_url = reverse_lazy('common:user')
