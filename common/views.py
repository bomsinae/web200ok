import asyncio
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, UserUpdateForm
from monitor.models import Http, HttpResult
import openpyxl
from django.http import HttpResponse
from telegram import Bot


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


async def send_telegram(message):
    TELEGRAM_TOKEN = "7513739190:AAFjoeDKBUxO_-5pl1Vcn7dY4_3hawDqdd4"
    CHAT_ID = 412105130
    bot = Bot(TELEGRAM_TOKEN)
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="HTML"
        )
        print(f"텔레그램 메시지 전송 성공: {message}")
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # 비밀번호 설정
            user.is_active = False  # 관리자 승인이 필요하도록 비활성화
            user.save()
            # 가입 후 관리자에게 텔레그램(412105130)으로 알림을 보내는 로직 추가
            asyncio.run(send_telegram(
                f"[URL모니터 회원가입 요청]\nID: {user.username}"))
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


@login_required
def abnormal_url_excel_download(request):
    """
    비정상 URL 리스트를 엑셀로 다운로드
    """
    from django.db.models import Subquery, OuterRef
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

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '비정상 URL'
    ws.append(['Account', 'Label', 'URL', '상태',
              '응답코드', '응답시간', '오류메시지', '검사일시'])
    for result in http_results:
        ws.append([
            result.http.account.name if hasattr(
                result.http, 'account') else '',
            result.http.label,
            result.http.url,
            result.get_status_display(),
            result.response_code,
            result.response_time,
            result.error_message,
            result.checked_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="abnormal_url_list.xlsx"'
    wb.save(response)
    return response
