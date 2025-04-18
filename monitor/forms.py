from django import forms
from monitor.models import Http


class HttpForm(forms.ModelForm):
    class Meta:
        model = Http
        fields = ['label', 'url', 'keyword', 'max_response_time', 'is_active']
        widgets = {
            'url': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'keyword': forms.TextInput(attrs={'class': 'form-control'}),
            'max_response_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'label': '라벨',
            'url': 'URL',
            'keyword': '키워드',
            'max_response_time': '최대응답시간(초)',
            'is_active': '사용',
        }
        help_texts = {
            'label': 'URL의 라벨을 입력하세요.',
            'url': '모니터링할 URL을 입력하세요.',
            'keyword': '응답에서 찾을 키워드를 입력하세요. (선택사항)',
            'max_response_time': '최대응답시간을 초 단위로 입력하세요.',
            'is_active': '모니터링을 활성화합니다.',
        }
        error_messages = {
            'label': {
                'required': '라벨을 입력하세요.',
            },
            'url': {
                'required': 'URL을 입력하세요.',
                'invalid': '유효한 URL을 입력하세요.',
            },
            'max_response_time': {
                'required': '최대응답시간을 입력하세요.',
                'invalid': '유효한 숫자를 입력하세요.',
            },
        }
        # Add any additional validation or customization here

        def clean(self):
            cleaned_data = super().clean()
            url = cleaned_data.get('url')
            max_response_time = cleaned_data.get('max_response_time')

            if not url:
                self.add_error('url', 'URL을 입력하세요.')
            if max_response_time <= 0:
                self.add_error('max_response_time', '최대응답시간은 0보다 커야 합니다.')

            return cleaned_data
