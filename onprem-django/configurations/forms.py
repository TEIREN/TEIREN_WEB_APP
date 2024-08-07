# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email  
from django.core.exceptions import ValidationError
from _auth.models import CustomUser
from _auth.models import FinevoUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        fields = ('username', 'email', 'password1', 'password2')  # 필요한 필드를 선택적으로 추가할 수 있습니다.
        model = CustomUser
        
        
class FinevoUserCreationForm(UserCreationForm):
    class Meta:
        fields = ('username', 'email', 'password1', 'password2')
        model = FinevoUser
