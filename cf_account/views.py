from typing import Any
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Account
from .forms import AccountForm, AccountUpdateForm

# Create your views here.

ACCOUNT_LIST_URL = 'cf_account:account'


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    queryset = Account.objects.order_by('-regdate')


class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'cf_account/account_form.html'
    success_url = reverse_lazy(ACCOUNT_LIST_URL)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountUpdateForm
    template_name = 'cf_account/account_form.html'
    success_url = reverse_lazy(ACCOUNT_LIST_URL)


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    success_url = reverse_lazy(ACCOUNT_LIST_URL)
