from django import forms
from django.contrib.auth.models import User


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean_email(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('이미 사용 중인 이메일입니다.')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:  # 최소 길이를 8자로 설정
            raise forms.ValidationError('패스워드는 최소 8자 이상이어야 합니다.')
        return password


class UserUpdateForm(forms.ModelForm):
    is_active = forms.BooleanField(required=False, label="사용자 활성화", widget=forms.CheckboxInput(
        attrs={'class': 'form-check-input'}))  # 활성화 체크박스
    first_name = forms.CharField(required=False, label="텔레그램 ID",
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['is_active', 'first_name']
