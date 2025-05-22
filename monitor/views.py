from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from .models import Http, HttpResult
from cf_account.models import Account
from .forms import HttpForm


@login_required
def http_list(request, account_id=None):
    """
    HTTP 모니터링 URL 목록
    """
    # 입력 파라미터
    page = request.GET.get('page', '1')
    kw = request.GET.get('kw', '')

    if account_id:
        account = get_object_or_404(Account, pk=account_id)
        # 특정 계정의 HTTP 모니터링 URL 목록
        http_list = Http.objects.filter(
            account_id=account_id).order_by('-created_at')
    else:
        http_list = Http.objects.all().order_by('-created_at')

    if kw:
        http_list = http_list.filter(
            Q(label__icontains=kw) |
            Q(url__icontains=kw) |
            Q(keyword__icontains=kw)
        ).distinct()

    http_list_count = http_list.count()
    active_http_list = http_list.filter(is_active=True).count()
    # 페이징처리
    per_page = 16
    paginator = Paginator(http_list, per_page)
    page_obj = paginator.get_page(page)

    context = {
        'http_list': page_obj,
        'page': page,
        'kw': kw,
        'account_id': account_id,
        'account': account if account_id else None,
        'http_list_count': http_list_count,
        'active_http_list': active_http_list,
    }

    return render(request, 'monitor/http_list.html', context)


@login_required
def http_update(request, http_id):
    """
    HTTP 모니터링 URL 수정
    """
    http = get_object_or_404(Http, pk=http_id)

    form = HttpForm(request.POST or None, instance=http)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('cf_account:account_http_list', account_id=http.account.id)
    else:
        form = HttpForm(instance=http)

    context = {
        'http': http,
        'form': form,
        'is_update': True,  # 업데이트 화면임을 표시하는 변수 추가
        'account': http.account,
    }

    return render(request, 'monitor/http_form.html', context)


@login_required
def http_create(request, account_id):
    """
    HTTP 모니터링 URL 생성
    """
    account = get_object_or_404(Account, pk=account_id)

    form = HttpForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            http = form.save(commit=False)
            http.account = account
            http.save()
            return redirect('cf_account:account_http_list', account_id=account.id)
    else:
        # Pre-select the account in the form
        form = HttpForm(initial={'account': account})

    context = {
        'form': form,
        'is_update': False,  # 생성 화면임을 표시하는 변수 추가
        'account': account,
    }

    return render(request, 'monitor/http_form.html', context)


@login_required
def http_delete(request, http_id):
    """
    HTTP 모니터링 URL 삭제
    """
    http = get_object_or_404(Http, pk=http_id)
    account = http.account
    if request.method == 'POST':
        http.delete()
        return redirect('cf_account:account_http_list', account_id=account.id)

    context = {
        'http': http,
        'account': account,
    }

    return render(request, 'monitor/http_delete.html', context)


@login_required
def monitor_result(request, http_id=None):
    """
    HTTP 모니터링 결과
    """
    if http_id is None:
        http = None
        # http_id가 없을 경우, 모든 결과를 보여줌
        results = HttpResult.objects.all().order_by('-checked_at')
    else:
        http = get_object_or_404(Http, pk=http_id)
        results = HttpResult.objects.filter(http=http).order_by('-checked_at')

    # 입력 파라미터
    page = request.GET.get('page', '1')
    kw = request.GET.get('kw', '')

    if kw:
        results = results.filter(
            Q(http__account__name__icontains=kw) |
            Q(http__label__icontains=kw) |
            Q(http__url__icontains=kw) |
            Q(http__keyword__icontains=kw) |
            Q(status__icontains=kw) |
            Q(response_code__icontains=kw) |
            Q(error_message__icontains=kw)
        ).distinct()

    # 페이징처리
    per_page = 16
    paginator = Paginator(results, per_page)
    page_obj = paginator.get_page(page)

    context = {
        'http': http,
        'results': page_obj,
        'page': page,
        'kw': kw,
    }

    return render(request, 'monitor/monitor_result.html', context)
