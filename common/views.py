from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, UserUpdateForm


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
