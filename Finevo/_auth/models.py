from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class CustomUser(AbstractUser):
    uuid = models.UUIDField(unique=True) # pk
    email = models.EmailField(unique=True)  # 이메일 필드 추가
    user_layout = models.CharField(max_length=50)
    db_name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)
    