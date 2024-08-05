# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email  
from django.core.exceptions import ValidationError
from .models import CustomUser
from .models import FinevoUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        fields = ('username', 'email', 'password1', 'password2')  # 필요한 필드를 선택적으로 추가할 수 있습니다.
        model = CustomUser
        
        
class FinevoUserCreationForm(forms.ModelForm):
    class Meta:
        fields = ('email', 'username', 'password')
        model = FinevoUser

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            validate_email(email)  # 이메일 형식 유효성 검사
        except ValidationError:
            raise forms.ValidationError("유효하지 않은 이메일 주소입니다.")
        return email
