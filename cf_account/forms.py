from django import forms
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account를 입력하세요'}),
        }

        labels = {
            'name': 'Account',
        }


class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'is_monitor']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account를 입력하세요'}),
            'is_monitor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'name': 'Account',
            'is_monitor': '모니터링 여부',
        }
