from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from .models import Http, HttpResult
from cf_account.models import Account
from .forms import HttpForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
import httpx
import openpyxl


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
        results = HttpResult.objects.all().order_by('-checked_at')
    else:
        http = get_object_or_404(Http, pk=http_id)
        results = HttpResult.objects.filter(http=http).order_by('-checked_at')

    # abnormal_only 파라미터 처리
    abnormal_only = request.GET.get('abnormal_only')
    if abnormal_only:
        results = results.exclude(status='success')

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
        'abnormal_only': abnormal_only,
    }

    return render(request, 'monitor/monitor_result.html', context)


@csrf_exempt
def register_monitoring_url(request):
    """
    외부에서 account_name, zone_name, cname_flag를 받아 모니터링에 등록/삭제하는 API
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    try:
        data = json.loads(request.body)
        account_name = data.get('account_name')
        zone_name = data.get('zone_name')
        cname_flag = data.get('cname_flag', '').upper()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    if not account_name or not zone_name or not cname_flag:
        return JsonResponse({'error': 'account_name, zone_name, cname_flag required'}, status=400)
    try:
        account = Account.objects.get(name=account_name)
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    url = f"https://{zone_name}"
    if cname_flag == 'YES':
        if Http.objects.filter(url=url).exists():
            return JsonResponse({'error': 'URL already exists'}, status=400)
        # url 정상접속 체크 (5xx 에러면 등록하지 않음)
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(url)
                body_text = resp.text
            if 500 <= resp.status_code and 'cloudflare' in body_text.lower():
                return JsonResponse({'error': f'Cloudflare 5xx error detected (status {resp.status_code}), not registered'}, status=502)
        except Exception as e:
            return JsonResponse({'error': f'URL check failed: {str(e)}'}, status=502)
        http = Http(
            account=account,
            url=url,
            label=zone_name,
            max_response_time=30,
            is_active=True
        )
        http.save()
        return JsonResponse({'message': 'URL registered successfully'}, status=200)
    elif cname_flag == 'NO':
        qs = Http.objects.filter(url=url)
        if qs.exists():
            qs.delete()
            return JsonResponse({'message': 'URL deleted successfully'}, status=200)
        else:
            return JsonResponse({'message': 'URL not found, nothing to delete'}, status=200)
    else:
        return JsonResponse({'error': 'cname_flag must be YES or NO'}, status=400)


@login_required
def http_list_excel(request, account_id=None):
    """
    HTTP 모니터링 URL 목록을 엑셀로 다운로드
    """
    kw = request.GET.get('kw', '')
    if account_id:
        account = get_object_or_404(Account, pk=account_id)
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

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'HTTPs'
    # 헤더
    headers = ['Account', 'Label', 'URL', 'Keyword',
               'Max Response Time', 'Active', 'Created At']
    ws.append(headers)
    for http in http_list:
        ws.append([
            http.account.name,
            http.label,
            http.url,
            http.keyword,
            http.max_response_time,
            'Y' if http.is_active else 'N',
            http.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = 'https_list.xlsx'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response


@login_required
def monitor_result_excel(request, http_id=None):
    """
    모니터링 결과를 엑셀로 다운로드
    """
    if http_id is None:
        http = None
        results = HttpResult.objects.all().order_by('-checked_at')
    else:
        http = get_object_or_404(Http, pk=http_id)
        results = HttpResult.objects.filter(http=http).order_by('-checked_at')

    abnormal_only = request.GET.get('abnormal_only')
    if abnormal_only:
        results = results.exclude(status='success')

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

    # 최대 100만개까지만 엑셀로 저장
    results = results[:10000]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '모니터링결과'
    headers = ['Account', 'Label', 'URL',
               '상태', '응답코드', '응답시간', '오류메시지', '검사일시']
    ws.append(headers)
    for r in results:
        try:
            ws.append([
                r.http.account.name,
                r.http.label,
                r.http.url,
                r.get_status_display(),
                r.response_code if r.response_code is not None else '',
                f"{r.response_time:.3f}" if r.response_time is not None else '',
                r.error_message or '',
                r.checked_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        except Exception as e:
            print(f"Error appending row: {e}")
            continue
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = 'monitor_result.xlsx'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response
